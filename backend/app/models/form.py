from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin
from .enums import FieldTypeEnum


class FormTemplate(Base, TimestampMixin):

    __tablename__ = "form_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reply_on_accept: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))

    fields: Mapped[list["FormField"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="FormField.order",
    )


class FormField(Base, TimestampMixin):

    __tablename__ = "form_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    form_template_id: Mapped[int] = mapped_column(
        ForeignKey("form_templates.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[FieldTypeEnum] = mapped_column(
        Enum(FieldTypeEnum, name="field_type_enum"), nullable=False
    )

    regexp: Mapped[str | None] = mapped_column(String(500))
    min_value: Mapped[str | None] = mapped_column(String(64))  
    max_value: Mapped[str | None] = mapped_column(String(64))

    default_value: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    profile_key: Mapped[str | None] = mapped_column(String(40))

    meta: Mapped[dict | None] = mapped_column(JSONB)

    template: Mapped[FormTemplate] = relationship(back_populates="fields")
