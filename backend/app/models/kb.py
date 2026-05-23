from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class KbFaq(Base, TimestampMixin):

    __tablename__ = "kb_faq"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    question_en: Mapped[str | None] = mapped_column(String(500))
    answer_en: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(16), default="ru")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class KbDocument(Base, TimestampMixin):

    __tablename__ = "kb_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list | None] = mapped_column(JSONB)  # list[str]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"))
