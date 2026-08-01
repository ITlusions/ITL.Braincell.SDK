"""IntelReport Pydantic schemas"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IntelReportCreate(BaseModel):
    title: str
    summary: str | None = None
    content: str | None = None
    classification_level: str | None = "UNCLASSIFIED"
    tlp_level: str | None = "GREEN"
    source: str | None = None
    analyst: str | None = None
    confidence_score: float | None = 0.5
    report_date: datetime | None = None
    valid_until: datetime | None = None
    tags: list[str] | None = None
    ioc_refs: list[str] | None = None
    threat_actor_refs: list[str] | None = None
    incident_refs: list[str] | None = None
    mitre_techniques: list[str] | None = None
    meta_data: dict[str, Any] | None = None


    created_at: datetime | None = None
class IntelReportResponse(BaseModel):
    id: UUID
    title: str
    summary: str | None = None
    content: str | None = None
    classification_level: str | None = None
    tlp_level: str | None = None
    source: str | None = None
    analyst: str | None = None
    confidence_score: float | None = None
    report_date: datetime | None = None
    valid_until: datetime | None = None
    tags: list[str] | None = None
    ioc_refs: list[str] | None = None
    threat_actor_refs: list[str] | None = None
    incident_refs: list[str] | None = None
    mitre_techniques: list[str] | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
