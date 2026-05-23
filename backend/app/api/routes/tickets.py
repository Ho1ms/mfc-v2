"""Список разговоров для сотрудников (§8.3 ТЗ).

Тикет — это сообщение от студента «без ответа». Здесь мы собираем
список последних разговоров с признаком «есть неотвеченное».
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models.enums import MessageDirectionEnum
from ...models.message import Message
from ...models.user import User
from ...schemas.message import ConversationItem, TicketsOverview
from ..deps import CurrentPrincipal, require_staff

router = APIRouter()


@router.get("/overview", response_model=TicketsOverview)
def tickets_overview(
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_staff),
) -> TicketsOverview:
    """Сводная статистика для бейджа в навбаре."""
    # «Открытый тикет» = существуют входящие сообщения, после которых нет исходящего
    last_inbound = (
        select(Message.user_id, func.max(Message.created_at).label("last_in"))
        .where(Message.direction == MessageDirectionEnum.in_)
        .group_by(Message.user_id)
        .subquery()
    )
    last_outbound = (
        select(Message.user_id, func.max(Message.created_at).label("last_out"))
        .where(Message.direction == MessageDirectionEnum.out)
        .group_by(Message.user_id)
        .subquery()
    )

    open_q = (
        select(func.count())
        .select_from(last_inbound)
        .outerjoin(last_outbound, last_inbound.c.user_id == last_outbound.c.user_id)
        .where(
            (last_outbound.c.last_out.is_(None))
            | (last_outbound.c.last_out < last_inbound.c.last_in)
        )
    )
    open_count = db.execute(open_q).scalar_one()
    return TicketsOverview(open_count=open_count, unread_count=open_count)


@router.get("/conversations", response_model=list[ConversationItem])
def list_conversations(
    only_open: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_staff),
) -> list[ConversationItem]:
    """Список последних разговоров. Сортировка — по дате последнего сообщения."""

    last_msg_subq = (
        select(
            Message.user_id,
            func.max(Message.created_at).label("last_at"),
        )
        .group_by(Message.user_id)
        .subquery()
    )

    last_in_subq = (
        select(
            Message.user_id,
            func.max(Message.created_at).label("last_in"),
        )
        .where(Message.direction == MessageDirectionEnum.in_)
        .group_by(Message.user_id)
        .subquery()
    )
    last_out_subq = (
        select(
            Message.user_id,
            func.max(Message.created_at).label("last_out"),
        )
        .where(Message.direction == MessageDirectionEnum.out)
        .group_by(Message.user_id)
        .subquery()
    )

    q = (
        select(
            User,
            last_msg_subq.c.last_at,
            last_in_subq.c.last_in,
            last_out_subq.c.last_out,
        )
        .join(last_msg_subq, last_msg_subq.c.user_id == User.id)
        .outerjoin(last_in_subq, last_in_subq.c.user_id == User.id)
        .outerjoin(last_out_subq, last_out_subq.c.user_id == User.id)
        .order_by(desc(last_msg_subq.c.last_at))
        .limit(limit)
    )

    rows = list(db.execute(q).all())
    user_ids = [u.id for u, *_ in rows]
    last_msgs: dict[int, Message] = {}
    if user_ids:
        # последнее сообщение в каждой переписке
        for user_id in user_ids:
            m = db.execute(
                select(Message)
                .where(Message.user_id == user_id)
                .order_by(desc(Message.created_at))
                .limit(1)
            ).scalar_one_or_none()
            if m is not None:
                last_msgs[user_id] = m

    out: list[ConversationItem] = []
    for u, last_at, last_in, last_out in rows:
        has_open = last_in is not None and (last_out is None or last_out < last_in)
        if only_open and not has_open:
            continue
        last = last_msgs.get(u.id)
        out.append(
            ConversationItem(
                user_id=u.id,
                first_name=u.first_name,
                last_name=u.last_name,
                username=u.username,
                photo_url=u.photo_url,
                system=u.system,
                last_message_text=(last.text if last else None),
                last_message_at=last_at,
                unread_count=1 if has_open else 0,
                has_open_ticket=has_open,
            )
        )
    return out
