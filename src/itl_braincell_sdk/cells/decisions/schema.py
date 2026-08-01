"""DesignDecision Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DecisionCreate(BaseModel):
    decision: str
    rationale: str | None = None
    impact: str | None = None
    status: str | None = "active"
    date_made: datetime | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class DecisionResponse(BaseModel):
    id: UUID
    decision: str
    rationale: str | None = None
    impact: str | None = None
    status: str | None = None
    date_made: datetime | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
