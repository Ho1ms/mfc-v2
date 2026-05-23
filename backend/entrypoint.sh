#!/usr/bin/env bash
# Запуск backend-контейнера:
#  - APP_ROLE=api     → applied migrations + uvicorn
#  - APP_ROLE=worker  → запуск воркера (миграции применяет api-инстанс)
#
# Миграции — идемпотентны (alembic upgrade head); если несколько api-реплик
# поднимаются одновременно, alembic берёт advisory lock в Postgres.
set -euo pipefail

ROLE="${APP_ROLE:-api}"

if [ "$ROLE" = "api" ]; then
  echo "[entrypoint] APP_ROLE=api → alembic upgrade head"
  alembic upgrade head
fi

echo "[entrypoint] exec $*"
exec "$@"
