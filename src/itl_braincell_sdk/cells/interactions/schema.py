"""Interaction Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InteractionCreate(BaseModel):
    conversation_id: UUID | None = None
    session_id: UUID | None = None
    role: str | None = None
    content: str | None = None
    message_type: str | None = None
    tokens_used: int | None = None
    timestamp: datetime | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class InteractionUpdate(BaseModel):
    role: str | None = None
    content: str | None = None
    message_type: str | None = None
    tokens_used: int | None = None
    meta_data: dict[str, Any] | None = None


class InteractionResponse(BaseModel):
    id: UUID
    conversation_id: UUID | None = None
    session_id: UUID | None = None
    role: str | None = None
    content: str | None = None
    message_type: str | None = None
    tokens_used: int | None = None
    timestamp: datetime | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
