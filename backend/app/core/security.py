from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from .config import settings


def create_access_token(payload: dict[str, Any], expires_min: int | None = None) -> str:
    exp = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_min or settings.JWT_EXPIRES_MIN)
    return jwt.encode({**payload, "exp": exp}, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
