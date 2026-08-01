"""Task Pydantic schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "open"
    priority: str = "medium"
    assignee: str | None = None
    project: str | None = None
    due_date: datetime | None = None
    completed_at: datetime | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class TaskResponse(TaskCreate):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    retention_days: int | None = None
    retain_reason: str | None = None
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
