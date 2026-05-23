from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.errors import bad_request, conflict, not_found
from ...db.session import get_db
from ...models.admin import Admin
from ...models.enums import AdminRoleEnum
from ..deps import CurrentPrincipal, require_admin

router = APIRouter()


class AdminOut(BaseModel):
    id: int
    max_user_id: str
    full_name: str
    role: AdminRoleEnum
    is_active: bool

    model_config = {"from_attributes": True}


class AdminCreateIn(BaseModel):
    max_user_id: str
    full_name: str
    role: AdminRoleEnum = AdminRoleEnum.employee
    is_active: bool = True


class AdminPatchIn(BaseModel):
    full_name: str | None = None
    role: AdminRoleEnum | None = None
    is_active: bool | None = None


@router.get("", response_model=list[AdminOut])
def list_admins(
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> list[Admin]:
    return list(db.execute(select(Admin).order_by(Admin.created_at.desc())).scalars())


@router.post("", response_model=AdminOut, status_code=201)
def create_admin(
    payload: AdminCreateIn,
    db: Session = Depends(get_db),
    _: CurrentPrincipal = Depends(require_admin),
) -> Admin:
    if not payload.max_user_id.strip() or not payload.full_name.strip():
        raise bad_request("max_user_id и full_name обязательны")
    existing = db.execute(
        select(Admin).where(Admin.max_user_id == payload.max_user_id)
    ).scalar_one_or_none()
    if existing:
        raise conflict("Сотрудник с таким max_user_id уже существует")
    admin = Admin(
        max_user_id=payload.max_user_id.strip(),
        full_name=payload.full_name.strip(),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.patch("/{admin_id}", response_model=AdminOut)
def patch_admin(
    admin_id: int,
    payload: AdminPatchIn,
    db: Session = Depends(get_db),
    me: CurrentPrincipal = Depends(require_admin),
) -> Admin:
    admin = db.get(Admin, admin_id)
    if admin is None:
        raise not_found("Сотрудник не найден")

    # Защита: нельзя самого себя деактивировать или понизить — иначе можно остаться без админов
    if admin.id == me.admin_id:
        if payload.is_active is False:
            raise bad_request("Нельзя деактивировать самого себя")
        if payload.role is not None and payload.role != AdminRoleEnum.admin:
            raise bad_request("Нельзя понизить самого себя")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(admin, k, v)
    db.commit()
    db.refresh(admin)
    return admin


@router.delete("/{admin_id}", status_code=204)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    me: CurrentPrincipal = Depends(require_admin),
):
    admin = db.get(Admin, admin_id)
    if admin is None:
        raise not_found("Сотрудник не найден")
    if admin.id == me.admin_id:
        raise bad_request("Нельзя удалить самого себя")
    db.delete(admin)
    db.commit()
