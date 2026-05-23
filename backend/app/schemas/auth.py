from datetime import date, datetime

from pydantic import BaseModel, Field

from ..models.enums import AdminRoleEnum, SystemEnum


class InitDataIn(BaseModel):
    """Тело /auth/max/validate — строка initData с подписью + контур."""

    init_data: str = Field(min_length=1, alias="initData")
    system: SystemEnum

    model_config = {"populate_by_name": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    expires_at: datetime


class StudentProfileOut(BaseModel):
    id: int
    user_id: str
    system: SystemEnum
    first_name: str | None = None
    last_name: str | None = None
    patronymic: str | None = None
    username: str | None = None
    photo_url: str | None = None
    language_code: str | None = None
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

    model_config = {"from_attributes": True}


class StudentLoginOut(BaseModel):
    token: TokenOut
    user: StudentProfileOut


class AdminProfileOut(BaseModel):
    id: int
    max_user_id: str
    full_name: str
    role: AdminRoleEnum
    is_active: bool


class AdminLoginOut(BaseModel):
    token: TokenOut
    admin: AdminProfileOut


class ContactIn(BaseModel):
    phone: str
    auth_date: int = Field(alias="authDate")
    hash: str
    system: SystemEnum

    model_config = {"populate_by_name": True}


class ContactOut(BaseModel):
    ok: bool
    phone: str
    verified: bool = True
