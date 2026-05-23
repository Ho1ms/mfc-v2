from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin
from .enums import SubmissionStatusEnum


class FormSubmission(Base, TimestampMixin):

    __tablename__ = "form_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    form_template_id: Mapped[int] = mapped_column(
        ForeignKey("form_templates.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    values: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    values_en: Mapped[dict | None] = mapped_column(JSONB)
    
    field_labels: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    status: Mapped[SubmissionStatusEnum] = mapped_column(
        Enum(SubmissionStatusEnum, name="submission_status_enum"),
        default=SubmissionStatusEnum.new,
        nullable=False,
        index=True,
    )

    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assignee_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL")
    )

    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)

    history: Mapped[list["SubmissionStatusHistory"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan", order_by="SubmissionStatusHistory.changed_at"
    )


class SubmissionStatusHistory(Base):

    __tablename__ = "submission_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("form_submissions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    from_status: Mapped[SubmissionStatusEnum | None] = mapped_column(
        Enum(SubmissionStatusEnum, name="submission_status_enum")
    )
    to_status: Mapped[SubmissionStatusEnum] = mapped_column(
        Enum(SubmissionStatusEnum, name="submission_status_enum"), nullable=False
    )
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    submission: Mapped[FormSubmission] = relationship(back_populates="history")
