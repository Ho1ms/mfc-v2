from __future__ import annotations

import logging
import time

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.security import decode_token
from ..db.session import SessionLocal
from ..models.audit import AuditLog

log = logging.getLogger(__name__)

_MUTATING = {"POST", "PUT", "PATCH", "DELETE"}
_SKIP_PREFIXES = (
    "/api/auth/",
    "/api/files",   # подписанные/публичные с подписью
    "/api/messages/ingress",
    "/api/messages/from-student",
)


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _principal_admin_id(request: Request) -> int | None:
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        return None
    return payload.get("admin_id")


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        path = request.url.path
        method = request.method
        should_audit = (
            method in _MUTATING
            and path.startswith("/api/")
            and not any(path.startswith(p) for p in _SKIP_PREFIXES)
        )

        if not should_audit:
            return await call_next(request)

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        admin_id = _principal_admin_id(request)
        # Не пишем действия студентов в audit — они не сотрудники.
        if admin_id is None:
            return response

        try:
            with SessionLocal() as db:
                db.add(
                    AuditLog(
                        admin_id=admin_id,
                        ip=_client_ip(request),
                        method=method,
                        path=path,
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                    )
                )
                db.commit()
        except Exception as e:  # noqa: BLE001
            log.warning("audit write failed: %s", e)

        return response
