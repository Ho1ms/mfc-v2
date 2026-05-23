"""Фоновая задача мониторинга Google-таблицы (§14, §15.3 ТЗ).

Каждые MONITORING_INTERVAL_SECONDS:
1. Читаем B:C.
2. Сравниваем со store (monitoring_states).
3. По каждому изменившемуся номеру — find активных подписчиков и enqueue_push.
4. Updates monitoring_states.

Идемпотентность — Redis-lock, чтобы не было двойных запусков.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from ..core.config import settings
from ..db.redis import redis_client
from ..db.session import SessionLocal
from ..models.monitoring import MonitoringState, MonitoringSubscription
from ..services.google_sheets import GoogleSheetsError, read_status_map
from ..services.push import enqueue_push

log = logging.getLogger(__name__)

LOCK_KEY = "mfc:monitoring:lock"
LOCK_TTL = 60  # секунд — больше времени работы одной итерации


def tick() -> None:
    got = redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL)
    if not got:
        log.debug("monitoring tick: another worker holds the lock, skipping")
        return

    try:
        try:
            statuses = read_status_map()
        except GoogleSheetsError as e:
            log.warning("google sheets read failed: %s", e)
            return

        log.info("monitoring tick: %s rows from sheet", len(statuses))

        with SessionLocal() as db:
            now = datetime.now(tz=timezone.utc)
            changed: list[tuple[str, str | None, str]] = []  # (number, old, new)

            for number, new_status in statuses.items():
                state = db.get(MonitoringState, number)
                if state is None:
                    db.add(
                        MonitoringState(
                            request_number=number, last_status=new_status, checked_at=now
                        )
                    )
                    # первый раз увидели — для подписчиков не считаем "изменением"
                    continue

                old_status = state.last_status
                state.checked_at = now
                if old_status != new_status:
                    state.last_status = new_status
                    changed.append((number, old_status, new_status))

            db.commit()

            for number, old_status, new_status in changed:
                subs = list(
                    db.execute(
                        select(MonitoringSubscription).where(
                            MonitoringSubscription.request_number == number,
                            MonitoringSubscription.is_active.is_(True),
                        )
                    ).scalars()
                )
                if not subs:
                    continue
                for sub in subs:
                    enqueue_push(
                        db,
                        user_id=sub.user_id,
                        kind="monitoring_changed",
                        payload={
                            "request_number": number,
                            "old_status": old_status,
                            "new_status": new_status,
                        },
                    )
            log.info("monitoring tick: %s changes, pushes sent", len(changed))
    finally:
        try:
            redis_client.delete(LOCK_KEY)
        except Exception as e:  # noqa: BLE001
            log.debug("redis unlock failed: %s", e)


def schedule_jobs(scheduler) -> None:
    """Регистрирует все задачи в переданном scheduler (APScheduler)."""
    scheduler.add_job(
        tick,
        "interval",
        seconds=settings.MONITORING_INTERVAL_SECONDS,
        id="monitoring_tick",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(tz=timezone.utc),
    )
