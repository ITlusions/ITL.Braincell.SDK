"""IOC Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IOCCreate(BaseModel):
    type: str
    value: str
    confidence: float | None = 0.5
    severity: str | None = "medium"
    status: str | None = "active"
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    expiry_date: datetime | None = None
    source: str | None = None
    tags: list[str] | None = None
    context: str | None = None
    incident_refs: list[str] | None = None
    threat_actor_refs: list[str] | None = None
    classification_level: str | None = "UNCLASSIFIED"
    tlp_level: str | None = "GREEN"
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class IOCResponse(BaseModel):
    id: UUID
    type: str
    value: str
    confidence: float | None = None
    severity: str | None = None
    status: str | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    expiry_date: datetime | None = None
    source: str | None = None
    tags: list[str] | None = None
    context: str | None = None
    incident_refs: list[str] | None = None
    threat_actor_refs: list[str] | None = None
    classification_level: str | None = None
    tlp_level: str | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
