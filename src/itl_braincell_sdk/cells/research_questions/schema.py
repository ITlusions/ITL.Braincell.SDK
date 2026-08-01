"""Research Questions cell — Pydantic schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ResearchQuestionCreate(BaseModel):
    question: str
    status: str = "pending"
    priority: str = "medium"
    context: Optional[str] = None
    answer: Optional[str] = None
    source: str = "manual"
    source_interaction_id: Optional[UUID] = None
    tags: list[str] = Field(default_factory=list)
    meta_data: dict = Field(default_factory=dict)


    created_at: datetime | None = None
class ResearchQuestionUpdate(BaseModel):
    question: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    context: Optional[str] = None
    answer: Optional[str] = None
    tags: Optional[list[str]] = None
    meta_data: Optional[dict] = None


class ResearchQuestionResponse(ResearchQuestionCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
