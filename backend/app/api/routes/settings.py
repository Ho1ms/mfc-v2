

from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.config import settings as app_settings
from ...core.errors import not_found, unauthorized
from ...core.security import decode_token
from ...db.session import get_db
from ...models.settings import AppSetting
from ..deps import CurrentPrincipal, require_admin

router = APIRouter()


class SettingOut(BaseModel):
    key: str
    value: str | None = None


class SettingIn(BaseModel):
    value: str | None = None


def _authorize_read(x_bot_token: str | None, authorization: str | None) -> None:
    """Доступ на чтение: X-Bot-Token (для бота) ИЛИ JWT (любая авторизованная роль)."""
    expected = app_settings.BOT_INTERNAL_API_TOKEN
    if x_bot_token and expected and x_bot_token == expected:
        return
    if x_bot_token and not expected and app_settings.APP_ENV != "production":
        # dev-режим без настроенного токена — пропускаем по X-Bot-Token любого значения
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise unauthorized("Нужна авторизация или X-Bot-Token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        decode_token(token)
    except jwt.PyJWTError as e:
        raise unauthorized(f"Невалидный токен: {e!s}") from e


@router.get("/{key}", response_model=SettingOut)
def get_setting(
    key: str,
    db: Session = Depends(get_db),
    x_bot_token: str | None = Header(default=None, alias="X-Bot-Token"),
    authorization: str | None = Header(default=None),
) -> SettingOut:
    _authorize_read(x_bot_token, authorization)
    item = db.get(AppSetting, key)
    # Отдаём 200 c value=null, чтобы бот мог гладко использовать дефолт
    return SettingOut(key=key, value=item.value if item else None)


@router.get("", response_model=list[SettingOut])
def list_settings(
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> list[SettingOut]:
    items = list(db.execute(select(AppSetting).order_by(AppSetting.key)).scalars())
    return [SettingOut(key=i.key, value=i.value) for i in items]


@router.put("/{key}", response_model=SettingOut)
def put_setting(
    key: str,
    payload: SettingIn,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> SettingOut:
    item = db.get(AppSetting, key)
    if item is None:
        item = AppSetting(key=key, value=payload.value)
        db.add(item)
    else:
        item.value = payload.value
    db.commit()
    db.refresh(item)
    return SettingOut(key=item.key, value=item.value)


@router.delete("/{key}", status_code=204)
def delete_setting(
    key: str,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
):
    item = db.get(AppSetting, key)
    if item is None:
        raise not_found("Настройка не найдена")
    db.delete(item)
    db.commit()
