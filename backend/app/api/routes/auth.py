from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.errors import bad_request, forbidden, unauthorized
from ...core.security import create_access_token
from ...db.session import get_db
from ...models.admin import Admin
from ...models.enums import SystemEnum
from ...models.user import User
from ...schemas.auth import (
    AdminLoginOut,
    AdminProfileOut,
    ContactIn,
    ContactOut,
    InitDataIn,
    StudentLoginOut,
    StudentProfileOut,
    TokenOut,
)
from ...services.max_validation import (
    InitDataValidationError,
    validate_contact,
    validate_init_data,
)
from ...services.rate_limit import rate_limit
from ..deps import CurrentPrincipal, get_current_principal, require_student

router = APIRouter()

# Защита auth-эндпоинтов от перебора по подписи (§16 ТЗ)
_auth_rl = rate_limit("auth_max", limit=20, window_seconds=60)


def _make_token(payload: dict) -> TokenOut:
    token = create_access_token(payload)
    return TokenOut(
        access_token=token,
        token_type="bearer",
        role=payload["role"],
        expires_at=datetime.now(tz=timezone.utc) + timedelta(minutes=settings.JWT_EXPIRES_MIN),
    )


@router.post(
    "/init-data/validate",
    response_model=StudentLoginOut,
    dependencies=[Depends(_auth_rl)],
)
def auth_inid_data_validate(payload: InitDataIn, db: Session = Depends(get_db)) -> StudentLoginOut:
    try:
        init = validate_init_data(payload.init_data, payload.system.value)
    except InitDataValidationError as e:
        raise unauthorized(str(e)) from e

    user = db.execute(
        select(User).where(User.user_id == init.user_id, User.system == payload.system)
    ).scalar_one_or_none()

    if user is None:
        user = User(
            user_id=init.user_id,
            system=payload.system,
            first_name=init.first_name,
            last_name=init.last_name,
            username=init.username,
            photo_url=init.photo_url,
            language_code=init.language_code,
        )
        db.add(user)
        db.flush()
    else:
        user.username = init.username or user.username
        user.photo_url = init.photo_url or user.photo_url
        user.language_code = init.language_code or user.language_code
        if not user.first_name and init.first_name:
            user.first_name = init.first_name
        if not user.last_name and init.last_name:
            user.last_name = init.last_name

    db.commit()
    db.refresh(user)

    token = _make_token(
        {
            "sub": f"u:{user.id}",
            "role": "student",
            "user_pk": user.id,
            "system": user.system.value,
        }
    )
    return StudentLoginOut(token=token, user=StudentProfileOut.model_validate(user, from_attributes=True))


@router.post(
    "/admin/login",
    response_model=AdminLoginOut,
    dependencies=[Depends(_auth_rl)],
)
def auth_admin_login(payload: InitDataIn, db: Session = Depends(get_db)) -> AdminLoginOut:
    """Авторизация сотрудника/админа через mini-app MAX.

    Mini-app должен передать сюда initData с start_param=admin_login.
    """
    try:
        init = validate_init_data(payload.init_data, 
                                  system="max"
                                #   system=payload.system.value
        )
    except InitDataValidationError as e:
        raise unauthorized(str(e)) from e

    if init.start_param and init.start_param != "admin_login":
        raise bad_request("Неверный start_param для входа в админку", code="bad_start_param")

    admin = db.execute(
        select(Admin).where(Admin.max_user_id == init.user_id, Admin.is_active.is_(True))
    ).scalar_one_or_none()

    if admin is None:
        raise forbidden("Этот аккаунт MAX не привязан к сотруднику МФЦ")

    token = _make_token(
        {
            "sub": f"a:{admin.id}",
            "role": admin.role.value,
            "admin_id": admin.id,
            "system": payload.system.value,
        }
    )
    return AdminLoginOut(token=token, admin=AdminProfileOut.model_validate(admin, from_attributes=True))


@router.post("/phone/verify", response_model=ContactOut)
def auth_phone_verify(
    payload: ContactIn,
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(require_student),
) -> ContactOut:
    """Подтверждение телефона из MAX (§4.7). Привязывает phone к текущему студенту."""
    user = db.get(User, p.user_id)
    if user is None:
        raise unauthorized("Студент не найден")

    ok = validate_contact(
        phone=payload.phone,
        auth_date=payload.auth_date,
        user_id=user.user_id,
        received_hash=payload.hash,
        system=payload.system.value,
    )
    if not ok:
        raise bad_request("Подпись контакта не совпадает", code="bad_contact_hash")

    user.phone = payload.phone
    user.phone_verified = True
    db.commit()
    return ContactOut(ok=True, phone=payload.phone, verified=True)


@router.get("/me")
def auth_me(
    db: Session = Depends(get_db),
    p: CurrentPrincipal = Depends(get_current_principal),
) -> dict:
    """Информация о текущем субъекте (для UI)."""
    if p.role == "student" and p.user_id:
        user = db.get(User, p.user_id)
        if user is None:
            raise unauthorized("Пользователь не найден")
        return {
            "role": "student",
            "user": StudentProfileOut.model_validate(user, from_attributes=True).model_dump(),
        }
    if p.is_staff and p.admin_id:
        admin = db.get(Admin, p.admin_id)
        if admin is None:
            raise unauthorized("Админ не найден")
        return {
            "role": p.role,
            "admin": AdminProfileOut.model_validate(admin, from_attributes=True).model_dump(),
        }
    raise unauthorized("Невозможно определить субъекта")
