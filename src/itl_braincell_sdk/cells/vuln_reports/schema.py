"""Pydantic schemas for VulnReport."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReproductionStep(BaseModel):
    step: int
    action: str
    expected: Optional[str] = None
    actual: Optional[str] = None


class VulnReportCreate(BaseModel):
    title: str
    internal_id: Optional[str] = None
    cve_candidate: Optional[str] = None
    cwe_refs: list[str] = Field(default_factory=list)
    owasp_category: Optional[str] = None

    vendor: Optional[str] = None
    product: Optional[str] = None
    affected_versions: Optional[str] = None
    affected_endpoints: list[str] = Field(default_factory=list)

    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    cvss_vector: Optional[str] = None
    attack_vector: Optional[str] = None
    privileges_required: Optional[str] = None
    user_interaction: Optional[str] = None
    impact_confidentiality: Optional[str] = None
    impact_integrity: Optional[str] = None
    impact_availability: Optional[str] = None

    summary: Optional[str] = None
    technical_details: Optional[str] = None
    impact_description: Optional[str] = None
    remediation: Optional[str] = None

    poc_snippet_refs: list[str] = Field(default_factory=list)
    capture_refs: list[str] = Field(default_factory=list)
    ioc_refs: list[str] = Field(default_factory=list)
    vuln_patch_refs: list[str] = Field(default_factory=list)

    environment: Optional[str] = None
    prerequisites: Optional[str] = None
    reproduction_steps: list[dict] = Field(default_factory=list)
    affected_artifacts: list[dict] = Field(default_factory=list)

    disclosure_timeline: dict = Field(default_factory=dict)
    bounty_program: Optional[str] = None
    program_url: Optional[str] = None
    submission_id: Optional[str] = None
    payout_amount: Optional[float] = None
    payout_currency: str = "USD"

    status: str = "draft"
    severity: str = "high"
    classification_level: str = "UNCLASSIFIED"
    tlp_level: str = "RED"

    tags: list[str] = Field(default_factory=list)
    meta_data: dict = Field(default_factory=dict)


    created_at: datetime | None = None
class VulnReportStatusUpdate(BaseModel):
    """Lightweight update for advancing report status and recording payout."""
    status: str
    submission_id: Optional[str] = None
    payout_amount: Optional[float] = None
    payout_currency: Optional[str] = None
    tlp_level: Optional[str] = None
    notes: Optional[str] = None


class VulnReportResponse(VulnReportCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    retention_days: int
    retain_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
