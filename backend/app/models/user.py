from datetime import date

from sqlalchemy import Boolean, Date, Enum, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin
from .enums import SystemEnum


class User(Base, TimestampMixin):
    """Студент Разделение по `system`."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("user_id", "system", name="uq_users_user_id_system"),)

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    system: Mapped[SystemEnum] = mapped_column(
        Enum(SystemEnum, name="system_enum"), index=True, nullable=False
    )

    last_name: Mapped[str | None] = mapped_column(String(120))
    first_name: Mapped[str | None] = mapped_column(String(120))
    patronymic: Mapped[str | None] = mapped_column(String(120))
    username: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(32))
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email: Mapped[str | None] = mapped_column(String(180))
    photo_url: Mapped[str | None] = mapped_column(String(512))
    language_code: Mapped[str | None] = mapped_column(String(16), default="ru")

    birth_date: Mapped[date | None] = mapped_column(Date)
    study_group: Mapped[str | None] = mapped_column(String(64))
    rut_personnel_number: Mapped[str | None] = mapped_column(String(64))

    ban_chat: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_chat_reason: Mapped[str | None] = mapped_column(Text)
    ban_forms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_forms_reason: Mapped[str | None] = mapped_column(Text)
    ban_app: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_app_reason: Mapped[str | None] = mapped_column(Text)
