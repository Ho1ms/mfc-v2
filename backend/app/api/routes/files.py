"""Файлы / вложения (§8.3, §16 ТЗ).

- POST /api/files — загрузка multipart (для админов и студентов).
- GET /api/files/{id} — отдача файла по подписанному URL (без авторизации, проверяется sig).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...core.errors import not_found
from ...db.session import get_db
from ...models.attachment import Attachment
from ...services.files import make_signed_url, open_file, store_file, verify_signed
from ...services.rate_limit import rate_limit
from ..deps import CurrentPrincipal, get_current_principal

router = APIRouter()

# 30 загрузок / мин — для админа bulk-загрузка вложений, для студента — анти-флуд.
_upload_rl = rate_limit("file_upload", limit=30, window_seconds=60)


@router.post("", dependencies=[Depends(_upload_rl)])
async def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(get_current_principal),
) -> dict:
    """Загрузить файл. Доступно любой авторизованной роли (студент/сотрудник/админ).

    Возвращает: { id, url, name, mime, size_bytes }
    """
    content = await file.read()
    original_name = file.filename or "file"
    storage_path, size_bytes = store_file(content, original_name=original_name)

    att = Attachment(
        storage_path=storage_path,
        original_name=original_name,
        mime=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        uploaded_by_admin_id=p.admin_id,
        uploaded_by_user_id=p.user_id,
    )
    db.add(att)
    db.commit()
    db.refresh(att)

    return {
        "id": att.id,
        "url": make_signed_url(att.id),
        "name": att.original_name,
        "mime": att.mime,
        "size_bytes": att.size_bytes,
    }


@router.get("/{file_id}")
def download(
    file_id: int,
    exp: int = Query(...),
    sig: str = Query(...),
    db: Session = Depends(get_db),
) -> Response:
    verify_signed(file_id, exp, sig)
    att = db.get(Attachment, file_id)
    if att is None:
        raise not_found("Файл не найден")
    abs_path = open_file(att.storage_path)
    return FileResponse(
        path=str(abs_path),
        media_type=att.mime,
        filename=att.original_name,
    )
