"""Простой Redis-based rate-limiter (§16 ТЗ).

Скользящее окно через `INCR key + EXPIRE key window`. Если значение превышает limit —
кидаем ApiError 429. Используется в зависимостях FastAPI.
"""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request

from ..core.errors import ApiError
from ..db.redis import redis_client

log = logging.getLogger(__name__)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


def rate_limit(
    name: str,
    *,
    limit: int,
    window_seconds: int,
    key_func: Callable[[Request], str] | None = None,
):


    def _resolve_key(request: Request) -> str:
        if key_func is not None:
            return key_func(request)
        return _client_ip(request)

    def _dep(request: Request) -> None:
        try:
            key = f"rl:{name}:{_resolve_key(request)}"
            n = redis_client.incr(key)
            if n == 1:
                redis_client.expire(key, window_seconds)
            if n > limit:
                ttl = redis_client.ttl(key)
                raise ApiError(
                    code="rate_limited",
                    message="Слишком много запросов, попробуйте позже",
                    status_code=429,
                    retry_after=ttl if isinstance(ttl, int) and ttl > 0 else window_seconds,
                )
        except ApiError:
            raise
        except Exception as e:  # noqa: BLE001
            # Если redis недоступен — НЕ блокируем сервис, просто логируем
            log.warning("rate_limit %s: redis error: %s", name, e)

    return _dep
