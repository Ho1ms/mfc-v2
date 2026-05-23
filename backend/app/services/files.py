"""Файловое хранилище и подписанные URL для вложений (§8.3, §16 ТЗ).

Файлы хранятся локально в UPLOADS_DIR. Доступ выдаётся через подписанный URL вида:

    /api/files/{id}?exp=<unix>&sig=<hex>

где sig = HMAC_SHA256(key=JWT_SECRET, message=f"{id}.{exp}").
По истечении exp подпись становится невалидной.

Прямой листинг и угадывание путей невозможны — только id + правильная подпись.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from pathlib import Path

from ..core.config import settings
from ..core.errors import bad_request, not_found

log = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 60 * 60 * 24 * 30 # 30 дней
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 МБ 


def _ensure_dir() -> Path:
    base = Path(settings.UPLOADS_DIR)
    base.mkdir(parents=True, exist_ok=True)
    return base


def store_file(content: bytes, *, original_name: str) -> tuple[str, int]:
    """Сохранить байты в UPLOADS_DIR со случайным именем. Возвращает (relative_path, size)."""
    if len(content) > MAX_UPLOAD_BYTES:
        raise bad_request(f"Файл больше {MAX_UPLOAD_BYTES // (1024 * 1024)} МБ", code="file_too_large")
    if len(content) == 0:
        raise bad_request("Пустой файл")

    base = _ensure_dir()

    token = secrets.token_hex(16)
    subdir = base / token[:2]
    subdir.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_name).suffix.lower() if original_name else ""

    if suffix in {".exe", ".bat", ".cmd", ".com", ".scr"}:
        raise bad_request("Запрещённый тип файла", code="file_type")

    name = f"{token}{suffix}"
    rel_path = f"{token[:2]}/{name}"
    abs_path = subdir / name
    abs_path.write_bytes(content)
    return rel_path, len(content)


def open_file(relative_path: str) -> Path:
    base = _ensure_dir()

    abs_path = (base / relative_path).resolve()
    base_resolved = base.resolve()
    if not str(abs_path).startswith(str(base_resolved) + ("/" if not str(base_resolved).endswith("/") else "")) and abs_path != base_resolved:
        import os

        if os.path.commonpath([str(abs_path), str(base_resolved)]) != str(base_resolved):
            raise not_found("Файл не найден")
    if not abs_path.exists() or not abs_path.is_file():
        raise not_found("Файл не найден")
    return abs_path


def make_signed_url(file_id: int, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    exp = int(time.time()) + ttl_seconds
    sig = _sign(file_id, exp)
    return f"/api/files/{file_id}?exp={exp}&sig={sig}"


def verify_signed(file_id: int, exp: int, sig: str) -> None:
    if exp < int(time.time()):
        raise bad_request("Ссылка просрочена", code="link_expired")
    expected = _sign(file_id, exp)
    if not hmac.compare_digest(expected, sig):
        raise bad_request("Невалидная подпись", code="bad_signature")


def _sign(file_id: int, exp: int) -> str:
    msg = f"{file_id}.{exp}".encode("utf-8")
    return hmac.new(settings.JWT_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()
