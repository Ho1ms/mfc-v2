"""Точка входа воркера (APScheduler). Запускается контейнером `worker`."""

from __future__ import annotations

import logging
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

from ..core.logging import setup_logging
from . import push_outbox as push_outbox_jobs
from .monitoring import schedule_jobs as schedule_monitoring

log = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    log.info("worker: starting APScheduler")
    scheduler = BlockingScheduler(timezone="UTC")
    schedule_monitoring(scheduler)
    push_outbox_jobs.schedule_jobs(scheduler)

    def _graceful(*_):
        log.info("worker: shutdown")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _graceful)
    signal.signal(signal.SIGINT, _graceful)

    scheduler.start()


if __name__ == "__main__":
    main()
