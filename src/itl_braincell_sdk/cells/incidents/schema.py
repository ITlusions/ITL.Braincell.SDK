"""SecurityIncident Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TimelineEntry(BaseModel):
    timestamp: datetime
    event: str
    analyst: str | None = None


class IncidentCreate(BaseModel):
    title: str
    description: str | None = None
    severity: str | None = "medium"
    status: str | None = "open"
    attack_vector: str | None = None
    affected_assets: list[str] | None = None
    mitre_tactics: list[str] | None = None
    threat_actor_name: str | None = None
    classification_level: str | None = "UNCLASSIFIED"
    tlp_level: str | None = "GREEN"
    detected_at: datetime | None = None
    contained_at: datetime | None = None
    resolved_at: datetime | None = None
    ioc_refs: list[str] | None = None
    timeline: list[dict[str, Any]] | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class IncidentResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    attack_vector: str | None = None
    affected_assets: list[str] | None = None
    mitre_tactics: list[str] | None = None
    threat_actor_name: str | None = None
    classification_level: str | None = None
    tlp_level: str | None = None
    detected_at: datetime | None = None
    contained_at: datetime | None = None
    resolved_at: datetime | None = None
    ioc_refs: list[str] | None = None
    timeline: list[dict[str, Any]] | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
