"""Notes cell — Pydantic schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    source: str = "manual"
    meta_data: dict = Field(default_factory=dict)


    created_at: datetime | None = None
class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None
    source: Optional[str] = None
    meta_data: Optional[dict] = None


class NoteResponse(NoteCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
