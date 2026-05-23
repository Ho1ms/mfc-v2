from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from ..models.enums import SubmissionStatusEnum


class SubmissionIn(BaseModel):
    form_template_id: int
    values: dict[str, Any] = Field(default_factory=dict)  # field_id (str) -> value
    idempotency_key: str | None = None


class StatusHistoryOut(BaseModel):
    id: int
    from_status: SubmissionStatusEnum | None
    to_status: SubmissionStatusEnum
    changed_by: int | None
    changed_at: datetime
    comment: str | None = None

    model_config = {"from_attributes": True}


class SubmitterOut(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    patronymic: str | None = None
    username: str | None = None
    photo_url: str | None = None
    user_id: str | None = None
    system: str | None = None
    birth_date: date | None = None
    study_group: str | None = None
    phone: str | None = None
    phone_verified: bool = False
    email: str | None = None


class SubmissionOut(BaseModel):
    id: int
    form_template_id: int
    user_id: int
    values: dict[str, Any]
    values_en: dict[str, Any] | None = None
    field_labels: dict[str, Any] = Field(default_factory=dict)
    status: SubmissionStatusEnum
    created_at: datetime
    taken_at: datetime | None = None
    closed_at: datetime | None = None
    assignee_admin_id: int | None = None

    model_config = {"from_attributes": True}


class SubmissionDetailed(SubmissionOut):
    history: list[StatusHistoryOut] = Field(default_factory=list)
    submitter: SubmitterOut | None = None
    form_name: str | None = None


class StatusPatchIn(BaseModel):
    status: SubmissionStatusEnum
    comment: str | None = None
