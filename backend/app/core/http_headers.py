"""Security-заголовки + correlation X-Request-ID.

Сознательно НЕ выставляем CSP здесь — для админки и mini-app нужны разные политики
(админка — `frame-ancestors 'none'`, mini-app — разрешить MAX). CSP лучше задаётся
на reverse-proxy перед фронтами, где известно, что именно отдаётся.
"""

from __future__ import annotations

import contextvars
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Текущий request_id — доступен из логов через contextvar.
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):  
        response: Response = await call_next(request)
        h = response.headers
        # Запрещаем браузеру угадывать MIME — защита от XSS через подмену типа.
        h.setdefault("X-Content-Type-Options", "nosniff")
        # Referrer — только origin между разными сайтами.
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # Permissions Policy — выключаем заведомо ненужные API (камера/гео и т.п.).
        h.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
        )
        # HSTS — имеет смысл только если терминируем https прямо здесь. На проде
        # обычно ставит reverse-proxy; но дублирующий заголовок не повредит.
        h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        # Сам сайт API в iframe не отдаём.
        h.setdefault("X-Frame-Options", "DENY")
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Берёт X-Request-ID из заголовка или генерит — кладёт в contextvar + ответ."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_var.set(rid)
        try:
            response: Response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers.setdefault("X-Request-ID", rid)
        return response
