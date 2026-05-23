from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base, TimestampMixin


class AppSetting(Base, TimestampMixin):

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text)
