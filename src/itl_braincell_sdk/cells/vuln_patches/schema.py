"""Pydantic schemas for VulnPatch."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VulnPatchCreate(BaseModel):
    title: str
    description: Optional[str] = None

    language: Optional[str] = None
    category: Optional[str] = None

    severity: str = "high"
    confidence_score: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)

    vulnerable_code: str
    patched_code: str
    patch_explanation: Optional[str] = None

    cve_refs: list[str] = Field(default_factory=list)
    cwe_refs: list[str] = Field(default_factory=list)
    owasp_refs: list[str] = Field(default_factory=list)

    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    meta_data: dict = Field(default_factory=dict)


    created_at: datetime | None = None
class VulnPatchResponse(VulnPatchCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    retention_days: int
    retain_reason: Optional[str] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
