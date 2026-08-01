"""Persons Pydantic schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PersonCreate(BaseModel):
    name: str
    role: str | None = None
    responsibilities: list[str] | None = None
    contact_info: str | None = None
    team: str | None = None
    source_interaction_id: UUID | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class PersonResponse(PersonCreate):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    retention_days: int | None = None
    retain_reason: str | None = None
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
