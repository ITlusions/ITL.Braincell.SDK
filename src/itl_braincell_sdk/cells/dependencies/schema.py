"""Dependency Pydantic schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DependencyCreate(BaseModel):
    name: str
    version: str
    ecosystem: str | None = None
    project: str | None = None
    license: str | None = None
    status: str = "ok"
    cve_refs: list[str] | None = None
    upgrade_to: str | None = None
    notes: str | None = None
    last_checked_at: datetime | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class DependencyResponse(DependencyCreate):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    retention_days: int | None = None

    model_config = ConfigDict(from_attributes=True)
