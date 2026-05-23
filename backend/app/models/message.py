from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin
from .admin import Admin
from .enums import MessageDirectionEnum, SystemEnum


class Message(Base, TimestampMixin):

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    system: Mapped[SystemEnum] = mapped_column(
    Enum(
        SystemEnum,
        name="system_enum",
        values_callable=lambda x: [e.value for e in x],
    ),
    index=True,
    nullable=False,
)
    direction: Mapped[MessageDirectionEnum] = mapped_column(
    Enum(
        MessageDirectionEnum,
        name="message_direction_enum",
        values_callable=lambda x: [e.value for e in x],
    ),
    nullable=False,
)
    text: Mapped[str | None] = mapped_column(Text)
    attachments: Mapped[list | None] = mapped_column(JSONB)

    is_ai_answered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_classification: Mapped[str | None] = mapped_column(String(120))

    replied_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL")
    )
    replied_by_admin: Mapped[Admin | None] = relationship("Admin", lazy="joined")

    external_id: Mapped[str | None] = mapped_column(String(120), unique=True, index=True)

    @property
    def replied_by_admin_name(self) -> str | None:
        return self.replied_by_admin.full_name if self.replied_by_admin else None
