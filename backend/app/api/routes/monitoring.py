"""Мониторинг заявок из Google-таблицы (§9.4 ТЗ)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...models.monitoring import MonitoringState, MonitoringSubscription
from ...schemas.monitoring import LookupOut, SubscribeIn, SubscribeOut, SubscriptionOut
from ...services.google_sheets import GoogleSheetsError, read_status_map
from ...services.rate_limit import rate_limit
from ..deps import CurrentPrincipal, require_student

router = APIRouter()

_lookup_rl = rate_limit("monitoring_lookup", limit=30, window_seconds=60)


@router.get("/lookup", response_model=LookupOut, dependencies=[Depends(_lookup_rl)])
def lookup(
    request_number: str = Query(...),
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_student),
) -> LookupOut:
    # Сначала пробуем взять из кэша
    state = db.get(MonitoringState, request_number)
    status = state.last_status if state else None
    checked_at = state.checked_at if state else None

    if state is None:
        # Прямое чтение, чтобы пользователь сразу получил ответ
        try:
            statuses = read_status_map()
            status = statuses.get(request_number)
        except GoogleSheetsError:
            status = None

    sub = db.execute(
        select(MonitoringSubscription).where(
            MonitoringSubscription.user_id == p.user_id,
            MonitoringSubscription.request_number == request_number,
            MonitoringSubscription.is_active.is_(True),
        )
    ).scalar_one_or_none()

    return LookupOut(
        request_number=request_number,
        status=status,
        checked_at=checked_at,
        is_subscribed=sub is not None,
    )


@router.get("/subscription", response_model=SubscriptionOut)
def my_subscription(
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_student),
) -> SubscriptionOut:

    sub = db.execute(
        select(MonitoringSubscription)
        .where(
            MonitoringSubscription.user_id == p.user_id,
            MonitoringSubscription.is_active.is_(True),
        )
        .order_by(MonitoringSubscription.updated_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if sub is None:
        return SubscriptionOut(is_active=False)

    state = db.get(MonitoringState, sub.request_number)
    return SubscriptionOut(
        request_number=sub.request_number,
        is_active=True,
        last_status=state.last_status if state else None,
        checked_at=state.checked_at if state else None,
    )


@router.post("/subscribe", response_model=SubscribeOut)
def subscribe(
    payload: SubscribeIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_student),
) -> SubscribeOut:
    sub = db.execute(
        select(MonitoringSubscription).where(
            MonitoringSubscription.user_id == p.user_id,
            MonitoringSubscription.request_number == payload.request_number,
        )
    ).scalar_one_or_none()

    if sub is None:
        from ...models.user import User
        u = db.get(User, p.user_id)
        sub = MonitoringSubscription(
            user_id=p.user_id,
            system=u.system,
            request_number=payload.request_number,
            is_active=True,
        )
        db.add(sub)
    else:
        sub.is_active = True

    db.commit()
    return SubscribeOut(request_number=payload.request_number, is_active=True)


@router.post("/unsubscribe", response_model=SubscribeOut)
def unsubscribe(
    payload: SubscribeIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_student),
) -> SubscribeOut:
    db.execute(
        update(MonitoringSubscription)
        .where(
            MonitoringSubscription.user_id == p.user_id,
            MonitoringSubscription.request_number == payload.request_number,
        )
        .values(is_active=False)
    )
    db.commit()
    return SubscribeOut(request_number=payload.request_number, is_active=False)
