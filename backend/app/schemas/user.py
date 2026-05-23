from datetime import date, datetime

from pydantic import BaseModel

from ..models.enums import SystemEnum


class ProfileOut(BaseModel):
    id: int
    user_id: str
    system: SystemEnum
    first_name: str | None = None
    last_name: str | None = None
    patronymic: str | None = None
    username: str | None = None
    phone: str | None = None
    phone_verified: bool = False
    email: str | None = None
    photo_url: str | None = None
    language_code: str | None = None
    birth_date: date | None = None
    study_group: str | None = None
    rut_personnel_number: str | None = None
    ban_chat: bool = False
    ban_chat_reason: str | None = None
    ban_forms: bool = False
    ban_forms_reason: str | None = None
    ban_app: bool = False
    ban_app_reason: str | None = None

    model_config = {"from_attributes": True}


class ProfilePatchIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    patronymic: str | None = None
    birth_date: date | None = None
    study_group: str | None = None
    email: str | None = None


class UserSummary(BaseModel):
    id: int
    user_id: str
    system: SystemEnum
    first_name: str | None = None
    last_name: str | None = None
    patronymic: str | None = None
    username: str | None = None
    photo_url: str | None = None
    phone: str | None = None
    phone_verified: bool = False
    email: str | None = None
    birth_date: date | None = None
    study_group: str | None = None
    ban_chat: bool = False
    ban_chat_reason: str | None = None
    ban_forms: bool = False
    ban_forms_reason: str | None = None
    ban_app: bool = False
    ban_app_reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BanPatchIn(BaseModel):
    """Управление блокировками — только админ."""

    ban_chat: bool | None = None
    ban_chat_reason: str | None = None
    ban_forms: bool | None = None
    ban_forms_reason: str | None = None
    ban_app: bool | None = None
    ban_app_reason: str | None = None


class RutLinkOut(BaseModel):
    """Заглушка привязки табельного номера РУТ (МИИТ) (§9.6 ТЗ)."""

    status: str = "in_development"
    message: str = "Привязка табельного номера РУТ (МИИТ) пока в разработке."
