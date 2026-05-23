from datetime import datetime

from pydantic import BaseModel


class FaqOut(BaseModel):
    id: int
    question: str
    answer: str
    question_en: str | None = None
    answer_en: str | None = None
    is_active: bool
    order: int

    model_config = {"from_attributes": True}


class FaqIn(BaseModel):
    question: str
    answer: str
    question_en: str | None = None
    answer_en: str | None = None
    is_active: bool = True
    order: int = 0


class FaqPatch(BaseModel):
    question: str | None = None
    answer: str | None = None
    question_en: str | None = None
    answer_en: str | None = None
    is_active: bool | None = None
    order: int | None = None


class KbDocumentOut(BaseModel):
    id: int
    topic: str
    content: str
    tags: list[str] | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class KbDocumentIn(BaseModel):
    topic: str
    content: str
    tags: list[str] | None = None
    is_active: bool = True


class KbDocumentPatch(BaseModel):
    topic: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class KbBulkIn(BaseModel):
    """Загрузка JSON-базы знаний (§5.9 ТЗ). Каждый элемент — KbDocumentIn."""

    documents: list[KbDocumentIn]
    replace: bool = False  # если true — старые документы удалить
