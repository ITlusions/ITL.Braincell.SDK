"""Conversation Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    session_id: UUID | None = None
    topic: str | None = None
    summary: str | None = None
    timestamp: datetime | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class ConversationUpdate(BaseModel):
    topic: str | None = None
    summary: str | None = None
    meta_data: dict[str, Any] | None = None


class ConversationResponse(BaseModel):
    id: UUID
    session_id: UUID | None = None
    topic: str | None = None
    summary: str | None = None
    timestamp: datetime | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
