from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import Float, cast, select
from sqlalchemy.orm import Session, selectinload

from ...core.errors import bad_request, conflict, forbidden, not_found
from ...db.session import get_db
from ...models.form import FormField, FormTemplate
from ...models.submission import FormSubmission, SubmissionStatusHistory
from ...models.enums import FieldTypeEnum, SubmissionStatusEnum
from ...models.user import User
from ...schemas.submission import (
    StatusHistoryOut,
    StatusPatchIn,
    SubmissionDetailed,
    SubmissionIn,
    SubmissionOut,
    SubmitterOut,
)
from ...services.form_validation import validate_values
from ...services.push import enqueue_push
from ...services.rate_limit import rate_limit
from ...services.translation import translate_values_to_en
from ...services.ws_hub import hub, staff_room
from ..deps import (
    CurrentPrincipal,
    get_current_principal,
    require_staff,
    require_student,
)


def _build_detailed(
    db: Session, sub: FormSubmission, *, include_history: bool = True
) -> SubmissionDetailed:
  
    u = db.get(User, sub.user_id)
    tpl = db.get(FormTemplate, sub.form_template_id)
    base = SubmissionOut.model_validate(sub, from_attributes=True).model_dump()
    return SubmissionDetailed(
        **base,
        history=(
            [StatusHistoryOut.model_validate(h, from_attributes=True) for h in sub.history]
            if include_history and sub.history is not None
            else []
        ),
        submitter=SubmitterOut(
            id=u.id,
            first_name=u.first_name,
            last_name=u.last_name,
            patronymic=u.patronymic,
            username=u.username,
            photo_url=u.photo_url,
            user_id=u.user_id,
            system=u.system.value if u.system else None,
            birth_date=u.birth_date,
            study_group=u.study_group,
            phone=u.phone,
            phone_verified=u.phone_verified,
            email=u.email,
        )
        if u
        else None,
        form_name=tpl.name if tpl else None,
    )

_submit_rl = rate_limit("submission_create", limit=10, window_seconds=60)
_status_rl = rate_limit("submission_status", limit=60, window_seconds=60)

router = APIRouter()



@router.get("", response_model=list[SubmissionDetailed])
def list_submissions(
    request: Request,
    form_id: int | None = Query(default=None),
    status: SubmissionStatusEnum | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(get_current_principal),
) -> list[SubmissionDetailed]:
    
    q = (
        select(FormSubmission)
        .options(
            selectinload(FormSubmission.history),
        )
        .order_by(FormSubmission.created_at.desc())
    )
    if p.role == "student":
        q = q.where(FormSubmission.user_id == p.user_id)
    else:
        if form_id:
            q = q.where(FormSubmission.form_template_id == form_id)
        if status:
            q = q.where(FormSubmission.status == status)

        # Фильтры по полям — только для сотрудников (студентам ни к чему)
        if form_id:
            fields = list(
                db.execute(
                    select(FormField).where(FormField.form_template_id == form_id)
                ).scalars()
            )
            for f in fields:
                key = f"f_{f.id}"
                if f.type == FieldTypeEnum.string:
                    v = request.query_params.get(key)
                    if v:
                        q = q.where(
                            FormSubmission.values[str(f.id)].astext.ilike(f"%{v}%")
                        )
                elif f.type == FieldTypeEnum.number:
                    v_from = request.query_params.get(f"{key}__from")
                    v_to = request.query_params.get(f"{key}__to")
                    try:
                        if v_from:
                            q = q.where(
                                cast(FormSubmission.values[str(f.id)].astext, Float) >= float(v_from)
                            )
                        if v_to:
                            q = q.where(
                                cast(FormSubmission.values[str(f.id)].astext, Float) <= float(v_to)
                            )
                    except (TypeError, ValueError):
                        pass
                elif f.type == FieldTypeEnum.date:
                    v_from = request.query_params.get(f"{key}__from")
                    v_to = request.query_params.get(f"{key}__to")
                    if v_from:
                        q = q.where(FormSubmission.values[str(f.id)].astext >= v_from)
                    if v_to:
                        q = q.where(FormSubmission.values[str(f.id)].astext <= v_to)
                elif f.type == FieldTypeEnum.checkbox:
                    v = request.query_params.get(key)
                    if v in ("true", "false"):
                        q = q.where(FormSubmission.values[str(f.id)].astext == v)

    q = q.limit(limit).offset(offset)
    rows = list(db.execute(q).scalars())

    form_ids = {r.form_template_id for r in rows}
    user_ids = {r.user_id for r in rows}
    forms = {
        f.id: f
        for f in db.execute(select(FormTemplate).where(FormTemplate.id.in_(form_ids))).scalars()
    }
    users = {u.id: u for u in db.execute(select(User).where(User.id.in_(user_ids))).scalars()}

    out: list[SubmissionDetailed] = []
    for r in rows:
        u = users.get(r.user_id)
        tpl = forms.get(r.form_template_id)
        base = SubmissionOut.model_validate(r, from_attributes=True).model_dump()
        out.append(
            SubmissionDetailed(
                **base,
                history=[],  
                submitter=SubmitterOut(
                    id=u.id,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    patronymic=u.patronymic,
                    username=u.username,
                    photo_url=u.photo_url,
                    user_id=u.user_id,
                    system=u.system.value if u.system else None,
                    birth_date=u.birth_date,
                    study_group=u.study_group,
                    phone=u.phone,
                    phone_verified=u.phone_verified,
                    email=u.email,
                )
                if u
                else None,
                form_name=tpl.name if tpl else None,
            )
        )
    return out


@router.get("/{submission_id}", response_model=SubmissionDetailed)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(get_current_principal),
) -> SubmissionDetailed:
    s = db.execute(
        select(FormSubmission)
        .options(selectinload(FormSubmission.history))
        .where(FormSubmission.id == submission_id)
    ).scalar_one_or_none()
    if s is None:
        raise not_found("Заявка не найдена")

    if p.role == "student" and s.user_id != p.user_id:
        raise forbidden("Чужая заявка")

    u = db.get(User, s.user_id)
    tpl = db.get(FormTemplate, s.form_template_id)
    return SubmissionDetailed(
        **SubmissionOut.model_validate(s, from_attributes=True).model_dump(),
        history=[StatusHistoryOut.model_validate(h, from_attributes=True) for h in s.history],
        submitter=SubmitterOut(
            id=u.id,
            first_name=u.first_name,
            last_name=u.last_name,
            patronymic=u.patronymic,
            username=u.username,
            photo_url=u.photo_url,
            user_id=u.user_id,
            system=u.system.value if u.system else None,
            birth_date=u.birth_date,
            study_group=u.study_group,
            phone=u.phone,
            phone_verified=u.phone_verified,
            email=u.email,
        )
        if u
        else None,
        form_name=tpl.name if tpl else None,
    )



_REQUIRED_PROFILE_FIELDS = (
    ("last_name", "Фамилия"),
    ("first_name", "Имя"),
    ("patronymic", "Отчество"),
    ("birth_date", "Дата рождения"),
    ("study_group", "Номер группы"),
)


def _ensure_profile_complete(user: User) -> None:
    missing: list[str] = []
    for attr, ru in _REQUIRED_PROFILE_FIELDS:
        v = getattr(user, attr, None)
        if v is None or (isinstance(v, str) and not v.strip()):
            missing.append(ru)
    if missing:
        raise bad_request(
            "Заполните профиль перед подачей формы: " + ", ".join(missing),
            code="profile_incomplete",
        )


@router.post(
    "",
    response_model=SubmissionDetailed,
    status_code=201,
    dependencies=[Depends(_submit_rl)],
)
async def create_submission(
    payload: SubmissionIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_student),
) -> SubmissionDetailed:
    
    user = db.get(User, p.user_id)

    if user is None:
        raise not_found("Профиль не найден")
    if user.ban_app:
        raise forbidden(user.ban_app_reason or "Доступ к приложению заблокирован", code="ban_app")
    if user.ban_forms:
        raise forbidden(user.ban_forms_reason or "Подача форм заблокирована", code="ban_forms")
    _ensure_profile_complete(user)

    if payload.idempotency_key:
        existing = db.execute(
            select(FormSubmission).where(FormSubmission.idempotency_key == payload.idempotency_key)
        ).scalar_one_or_none()
        if existing:
            if existing.user_id != p.user_id:
                raise conflict("Ключ идемпотентности уже использован", code="idempotency_collision")
            return existing

    tpl = db.execute(
        select(FormTemplate)
        .options(selectinload(FormTemplate.fields))
        .where(FormTemplate.id == payload.form_template_id, FormTemplate.is_active.is_(True))
    ).scalar_one_or_none()
    if tpl is None:
        raise not_found("Форма не найдена или неактивна")

    normalized = validate_values(tpl.fields, payload.values)
    values_en = translate_values_to_en(normalized)
    field_labels = {str(f.id): f.label for f in tpl.fields if str(f.id) in normalized}

    sub = FormSubmission(
        form_template_id=tpl.id,
        user_id=p.user_id,
        values=normalized,
        values_en=values_en,
        field_labels=field_labels,
        status=SubmissionStatusEnum.new,
        idempotency_key=payload.idempotency_key,
    )
    db.add(sub)
    db.flush()

    db.add(
        SubmissionStatusHistory(
            submission_id=sub.id,
            from_status=None,
            to_status=SubmissionStatusEnum.new,
            changed_by=None,
            changed_at=datetime.now(tz=timezone.utc),
            comment="Создание заявки",
        )
    )
    db.commit()
    db.refresh(sub)

    enqueue_push(
        db,
        user_id=p.user_id,
        kind="submission_created",
        payload={"submission_id": sub.id,  "reply_on_accept": f"<h1>{tpl.name} #{tpl.id}</h1>\n\n{tpl.reply_on_accept}"},
    )

    detailed = _build_detailed(db, sub, include_history=False)

    await hub.broadcast(
        staff_room(),
        {"type": "new_submission", "data": detailed.model_dump(mode="json")},
    )

    return detailed


_ALLOWED_TRANSITIONS: dict[SubmissionStatusEnum, set[SubmissionStatusEnum]] = {
    SubmissionStatusEnum.new: {SubmissionStatusEnum.in_work, SubmissionStatusEnum.rejected},
    SubmissionStatusEnum.in_work: {SubmissionStatusEnum.done, SubmissionStatusEnum.rejected},
    SubmissionStatusEnum.rejected: set(),
    SubmissionStatusEnum.done: set(),
}


@router.patch(
    "/{submission_id}/status",
    response_model=SubmissionDetailed,
    dependencies=[Depends(_status_rl)],
)
async def patch_status(
    submission_id: int,
    payload: StatusPatchIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_staff),
) -> SubmissionDetailed:
    s = db.get(FormSubmission, submission_id)
    if s is None:
        raise not_found("Заявка не найдена")

    if payload.status not in _ALLOWED_TRANSITIONS.get(s.status, set()):
        raise bad_request(
            f"Переход {s.status.value} → {payload.status.value} запрещён",
            code="bad_status_transition",
        )

    now = datetime.now(tz=timezone.utc)
    db.add(
        SubmissionStatusHistory(
            submission_id=s.id,
            from_status=s.status,
            to_status=payload.status,
            changed_by=p.admin_id,
            changed_at=now,
            comment=payload.comment
        )
    )

    s.status = payload.status
    if payload.status == SubmissionStatusEnum.in_work and not s.taken_at:
        s.taken_at = now
        s.assignee_admin_id = p.admin_id
    if payload.status in (SubmissionStatusEnum.done, SubmissionStatusEnum.rejected):
        s.closed_at = now

    db.commit()
    db.refresh(s)

    enqueue_push(
        db,
        user_id=s.user_id,
        kind="submission_status",
        payload={
            "submission_id": s.id,
            "status": s.status.value,
            "comment": payload.comment
        },
    )

    detailed = _build_detailed(db, s)

    await hub.broadcast(
        staff_room(),
        {"type": "submission_updated", "data": detailed.model_dump(mode="json")},
    )

    await hub.broadcast(
        f"user:{s.user_id}",
        {"type": "submission_updated", "data": detailed.model_dump(mode="json")},
    )

    return detailed
