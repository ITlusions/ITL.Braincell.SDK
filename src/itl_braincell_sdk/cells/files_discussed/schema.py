"""FileDiscussed Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FileDiscussedCreate(BaseModel):
    file_path: str
    description: str | None = None
    language: str | None = None
    purpose: str | None = None
    last_modified: datetime | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class FileDiscussedResponse(BaseModel):
    id: UUID
    file_path: str
    description: str | None = None
    language: str | None = None
    purpose: str | None = None
    last_modified: datetime | None = None
    discussion_count: int = 1
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
