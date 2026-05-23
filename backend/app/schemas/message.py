from datetime import datetime
from typing import Any

from pydantic import BaseModel

from ..models.enums import MessageDirectionEnum, SystemEnum


class AttachmentOut(BaseModel):
    url: str
    name: str | None = None
    mime: str | None = None
    size: int | None = None


class MessageOut(BaseModel):
    id: int
    user_id: int
    system: SystemEnum
    direction: MessageDirectionEnum
    text: str | None = None
    attachments: list[AttachmentOut] | None = None
    is_ai_answered: bool = False
    ai_classification: str | None = None
    replied_by_admin_id: int | None = None
    replied_by_admin_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IngressMessageIn(BaseModel):
    """Сообщение от бота — приём в backend."""

    user_id: str  # external (MAX) user_id
    system: SystemEnum
    text: str | None = None
    attachments: list[dict[str, Any]] | None = None
    external_id: str | None = None  # для идемпотентности
    language_code: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


class IngressMessageOut(BaseModel):
    message: MessageOut
    ai_answer: str | None = None  # если ответил AI — что ответить в чат


class StaffReplyIn(BaseModel):
    text: str | None = None
    # Список id вложений из POST /api/files. Перед отправкой backend заполнит url/name/mime/size.
    attachment_ids: list[int] | None = None
    attachments: list[dict[str, Any]] | None = None  # альтернативный вариант — внешние ссылки


class StudentMessageIn(BaseModel):
    """Сообщение от mini-app студента — если решим открыть отдельный экран чата."""

    text: str | None = None
    attachment_ids: list[int] | None = None
    attachments: list[dict[str, Any]] | None = None


class TicketsOverview(BaseModel):
    open_count: int
    unread_count: int


class ConversationItem(BaseModel):
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    system: SystemEnum
    last_message_text: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0
    has_open_ticket: bool = False
