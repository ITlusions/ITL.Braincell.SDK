"""ThreatActor Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ThreatActorCreate(BaseModel):
    name: str
    aliases: list[str] | None = None
    classification: str | None = None
    origin_country: str | None = None
    motivation: str | None = None
    sophistication: str | None = None
    ttps: list[str] | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    status: str | None = "active"
    confidence_score: float | None = 0.5
    stix_id: str | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class ThreatActorResponse(BaseModel):
    id: UUID
    name: str
    aliases: list[str] | None = None
    classification: str | None = None
    origin_country: str | None = None
    motivation: str | None = None
    sophistication: str | None = None
    ttps: list[str] | None = None
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    status: str | None = None
    confidence_score: float | None = None
    stix_id: str | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
