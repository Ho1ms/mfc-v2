from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.errors import bad_request, forbidden, not_found, unauthorized
from ...db.session import get_db
from ...models.admin import Admin
from ...models.enums import MessageDirectionEnum, SystemEnum
from ...models.message import Message
from ...models.user import User
from ...schemas.message import (
    IngressMessageIn,
    IngressMessageOut,
    MessageOut,
    StaffReplyIn,
    StudentMessageIn,
)
from ...models.attachment import Attachment
from ...services.ai import classify, find_answer
from ...services.files import make_signed_url
from ...services.push import enqueue_push
from ...services.rate_limit import rate_limit
from ...services.ws_hub import hub, staff_room, user_room
from ..deps import CurrentPrincipal, get_current_principal, require_staff, require_student

_student_msg_rl = rate_limit("student_msg", limit=20, window_seconds=60)
_staff_msg_rl = rate_limit("staff_msg", limit=120, window_seconds=60)
_ingress_rl = rate_limit("msg_ingress", limit=600, window_seconds=60)

log = logging.getLogger(__name__)

router = APIRouter()


def _resolve_attachments(
    db: Session,
    attachment_ids: list[int] | None,
    external_attachments: list[dict] | None,
) -> list[dict] | None:
  
    out: list[dict] = []
    if attachment_ids:
        rows = (
            db.execute(select(Attachment).where(Attachment.id.in_(attachment_ids))).scalars().all()
        )
        for a in rows:
            out.append(
                {
                    "id": a.id,
                    "url": make_signed_url(a.id),
                    "name": a.original_name,
                    "mime": a.mime,
                    "size": a.size_bytes,
                }
            )
    if external_attachments:
        for ext in external_attachments:
            if ext and ext.get("url"):
                out.append(ext)
    return out or None


def _check_internal_token(x_bot_token: str | None) -> None:
    expected = settings.BOT_INTERNAL_API_TOKEN
    if not expected:
        if settings.APP_ENV == "production":
            raise unauthorized("Internal bot token обязателен")
        return
    if x_bot_token != expected:
        raise unauthorized("Неверный internal bot token")


def _get_or_create_user_from_external(db: Session, payload: IngressMessageIn) -> User:
    user = db.execute(
        select(User).where(User.user_id == payload.user_id, User.system == payload.system)
    ).scalar_one_or_none()
    if user is None:
        user = User(
            user_id=payload.user_id,
            system=payload.system,
            first_name=payload.first_name,
            last_name=payload.last_name,
            username=payload.username,
            language_code=payload.language_code or "ru",
        )
        db.add(user)
        db.flush()
    else:
        if payload.first_name and not user.first_name:
            user.first_name = payload.first_name
        if payload.last_name and not user.last_name:
            user.last_name = payload.last_name
        if payload.username and not user.username:
            user.username = payload.username
        if payload.language_code:
            user.language_code = payload.language_code
    return user


@router.post(
    "/ingress",
    response_model=IngressMessageOut,
    dependencies=[Depends(_ingress_rl)],
)
async def ingress_message(
    payload: IngressMessageIn,
    db: Session = Depends(get_db),
    x_bot_token: str | None = Header(default=None, alias="X-Bot-Token"),
) -> IngressMessageOut:

    _check_internal_token(x_bot_token)

    # Идемпотентность
    if payload.external_id:
        existing = db.execute(
            select(Message).where(Message.external_id == payload.external_id)
        ).scalar_one_or_none()
        if existing:
            return IngressMessageOut(
                message=MessageOut.model_validate(existing, from_attributes=True),
                ai_answer=None,
            )

    user = _get_or_create_user_from_external(db, payload)

    classification = classify(payload.text or "")
    hit = find_answer(db, payload.text or "")

    incoming = Message(
        user_id=user.id,
        system=payload.system,
        direction=MessageDirectionEnum.in_,
        text=payload.text,
        attachments=payload.attachments,
        is_ai_answered=bool(hit),
        ai_classification=classification,
        external_id=payload.external_id,
    )
    db.add(incoming)
    db.flush()

    ai_answer: str | None = None
    outgoing: Message | None = None
    if hit:
        ai_answer = hit.answer
        outgoing = Message(
            user_id=user.id,
            system=payload.system,
            direction=MessageDirectionEnum.out,
            text=hit.answer,
            attachments=None,
            is_ai_answered=True,
            ai_classification=f"kb:{hit.document_id}",
        )
        db.add(outgoing)
        db.flush()

    db.commit()
    db.refresh(incoming)
    if outgoing is not None:
        db.refresh(outgoing)

    in_dto = MessageOut.model_validate(incoming, from_attributes=True).model_dump(mode="json")
    await hub.broadcast(user_room(user.id), {"type": "message", "data": in_dto})
    if outgoing is None:
        await hub.broadcast(
            staff_room(),
            {"type": "new_ticket", "user_id": user.id, "data": in_dto},
        )
    else:
        out_dto = MessageOut.model_validate(outgoing, from_attributes=True).model_dump(mode="json")
        await hub.broadcast(user_room(user.id), {"type": "message", "data": out_dto})

    return IngressMessageOut(
        message=MessageOut.model_validate(incoming, from_attributes=True),
        ai_answer=ai_answer,
    )


@router.get("", response_model=list[MessageOut])
def list_messages(
    user_id: int = Query(...),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(get_current_principal),
) -> list[Message]:
    if p.role == "student" and p.user_id != user_id:
        raise forbidden("Чужая переписка")
    q = (
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(q).scalars())

@router.post(
    "/to-user/{user_pk}",
    response_model=MessageOut,
    dependencies=[Depends(_staff_msg_rl)],
)
async def staff_reply(
    user_pk: int,
    payload: StaffReplyIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_staff),
) -> Message:
    attachments = _resolve_attachments(db, payload.attachment_ids, payload.attachments)
    if not payload.text and not attachments:
        raise bad_request("Пустое сообщение")
    user = db.get(User, user_pk)
    if user is None:
        raise not_found("Пользователь не найден")

    msg = Message(
        user_id=user.id,
        system=user.system,
        direction=MessageDirectionEnum.out,
        text=payload.text,
        attachments=attachments,
        replied_by_admin_id=p.admin_id,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    dto = MessageOut.model_validate(msg, from_attributes=True).model_dump(mode="json")
    await hub.broadcast(user_room(user.id), {"type": "message", "data": dto})

    await hub.broadcast(staff_room(), {"type": "ticket_answered", "user_id": user.id})

    admin = db.get(Admin, p.admin_id) if p.admin_id else None
    enqueue_push(
        db,
        user_id=user.id,
        kind="staff_message",
        payload={
            "text": payload.text or "",
            "admin_name": admin.full_name if admin else None,
            "attachments": attachments or [],
        },
    )

    return msg


# Сообщение от студента (на случай если будет отдельный экран чата в mini-app)
@router.post(
    "/from-student",
    response_model=MessageOut,
    dependencies=[Depends(_student_msg_rl)],
)
async def student_message(
    payload: StudentMessageIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_student),
) -> Message:
    user = db.get(User, p.user_id)
    if user is None:
        raise unauthorized("Студент не найден")
    if user.ban_app:
        raise forbidden(user.ban_app_reason or "Доступ к приложению заблокирован", code="ban_app")
    if user.ban_chat:
        raise forbidden(user.ban_chat_reason or "Чат заблокирован", code="ban_chat")

    attachments = _resolve_attachments(db, payload.attachment_ids, payload.attachments)
    if not payload.text and not attachments:
        raise bad_request("Пустое сообщение")

    msg = Message(
        user_id=user.id,
        system=user.system,
        direction=MessageDirectionEnum.in_,
        text=payload.text,
        attachments=attachments,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    dto = MessageOut.model_validate(msg, from_attributes=True).model_dump(mode="json")
    await hub.broadcast(user_room(user.id), {"type": "message", "data": dto})
    await hub.broadcast(staff_room(), {"type": "new_ticket", "user_id": user.id, "data": dto})
    return msg
