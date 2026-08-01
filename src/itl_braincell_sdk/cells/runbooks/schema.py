"""Runbook Pydantic schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RunbookStep(BaseModel):
    step: int
    title: str
    command: str | None = None
    expected_output: str | None = None
    notes: str | None = None


class RunbookCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    trigger: str | None = None
    prerequisites: str | None = None
    steps: list[dict[str, Any]] = []
    rollback_steps: list[dict[str, Any]] | None = None
    severity: str | None = None
    services: list[str] | None = None
    last_used_at: datetime | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class RunbookResponse(RunbookCreate):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    retention_days: int | None = None

    model_config = ConfigDict(from_attributes=True)
