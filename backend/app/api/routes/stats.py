

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models.enums import SubmissionStatusEnum
from ...models.form import FormTemplate
from ...models.submission import FormSubmission, SubmissionStatusHistory
from ...models.user import User
from ..deps import CurrentPrincipal, require_staff

router = APIRouter()


@router.get("/overview")
def overview(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_staff),
) -> dict:
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)

    # Bar: по формам
    bar_rows = db.execute(
        select(
            FormTemplate.id,
            FormTemplate.name,
            func.count(FormSubmission.id).label("cnt"),
        )
        .join(FormSubmission, FormSubmission.form_template_id == FormTemplate.id, isouter=True)
        .where(
            (FormSubmission.id.is_(None)) | (FormSubmission.created_at >= since),
        )
        .group_by(FormTemplate.id, FormTemplate.name)
        .order_by(FormTemplate.order, FormTemplate.id)
    ).all()
    bar = [{"form_id": r[0], "name": r[1], "count": int(r[2] or 0)} for r in bar_rows]

    # Timeseries (по дням)
    ts_rows = db.execute(
        select(
            func.date_trunc("day", FormSubmission.created_at).label("day"),
            func.count(FormSubmission.id),
        )
        .where(FormSubmission.created_at >= since)
        .group_by("day")
        .order_by("day")
    ).all()
    timeseries = [{"day": r[0].date().isoformat() if r[0] else None, "count": int(r[1])} for r in ts_rows]

    # KPI: среднее время new->in_work и in_work->done
    # из submission_status_history (changed_at)
    h = SubmissionStatusHistory
    new_to_work = db.execute(
        select(func.avg(
            (h.changed_at - FormSubmission.created_at)
        ))
        .join(FormSubmission, FormSubmission.id == h.submission_id)
        .where(h.to_status == SubmissionStatusEnum.in_work, FormSubmission.created_at >= since)
    ).scalar()

    avg_new_to_work_seconds = int(new_to_work.total_seconds()) if new_to_work else 0

    work_to_done = db.execute(
        select(func.avg(FormSubmission.closed_at - FormSubmission.taken_at))
        .where(
            FormSubmission.taken_at.isnot(None),
            FormSubmission.closed_at.isnot(None),
            FormSubmission.status == SubmissionStatusEnum.done,
            FormSubmission.created_at >= since,
        )
    ).scalar()
    avg_work_to_done_seconds = int(work_to_done.total_seconds()) if work_to_done else 0

    # Распределение по статусам
    by_status_rows = db.execute(
        select(FormSubmission.status, func.count(FormSubmission.id))
        .where(FormSubmission.created_at >= since)
        .group_by(FormSubmission.status)
    ).all()
    by_status = {row[0].value: int(row[1]) for row in by_status_rows}

    total = sum(by_status.values()) or 0
    rejected_share = (by_status.get("rejected", 0) / total) if total else 0.0

    # Конверсия (§ задача 6): сколько уникальных пользователей завели аккаунт
    # за окно и сколько из них дошли до подачи хотя бы одной заявки.
    users_total = int(
        db.execute(
            select(func.count(User.id)).where(User.created_at >= since)
        ).scalar() or 0
    )
    users_with_submission = int(
        db.execute(
            select(func.count(func.distinct(FormSubmission.user_id))).where(
                FormSubmission.created_at >= since
            )
        ).scalar() or 0
    )
    conversion_rate = (users_with_submission / users_total) if users_total else 0.0

    return {
        "days": days,
        "bar": bar,
        "timeseries": timeseries,
        "kpi": {
            "avg_new_to_work_seconds": avg_new_to_work_seconds,
            "avg_work_to_done_seconds": avg_work_to_done_seconds,
            "rejected_share": rejected_share,
            "total": total,
            "by_status": by_status,
            "users_total": users_total,
            "users_with_submission": users_with_submission,
            "conversion_rate": conversion_rate,
        },
    }
