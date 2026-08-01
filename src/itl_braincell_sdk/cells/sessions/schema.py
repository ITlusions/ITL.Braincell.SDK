"""MemorySession Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MemorySessionCreate(BaseModel):
    session_name: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = "active"
    conversation_ids: list[str] | None = None
    file_ids: list[str] | None = None
    summary: str | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class MemorySessionUpdate(BaseModel):
    session_name: str | None = None
    end_time: datetime | None = None
    status: str | None = None
    conversation_ids: list[str] | None = None
    file_ids: list[str] | None = None
    summary: str | None = None
    meta_data: dict[str, Any] | None = None


class MemorySessionResponse(BaseModel):
    id: UUID
    session_name: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = None
    conversation_ids: list[str] | None = None
    file_ids: list[str] | None = None
    summary: str | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
