from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin
from .enums import AdminRoleEnum


class Admin(Base, TimestampMixin):

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    max_user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[AdminRoleEnum] = mapped_column(
        Enum(AdminRoleEnum, name="admin_role_enum"), nullable=False, default=AdminRoleEnum.employee
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
