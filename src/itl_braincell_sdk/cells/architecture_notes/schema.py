"""ArchitectureNote Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArchitectureNoteCreate(BaseModel):
    component: str
    description: str | None = None
    type: str | None = None
    status: str | None = "active"
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class ArchitectureNoteResponse(BaseModel):
    id: UUID
    component: str
    description: str | None = None
    type: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
