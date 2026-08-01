"""KillChain Pydantic schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class KillChainPhase(BaseModel):
    """A single phase in a kill chain campaign."""

    phase: str                               # "reconnaissance" or "TA0043"
    order: int
    status: str = "planned"                  # planned / active / completed / skipped
    techniques: list[str] | None = None      # ["T1595.002"]
    tools_used: list[str] | None = None
    ioc_refs: list[str] | None = None        # IOC.value strings
    snippet_refs: list[str] | None = None    # CodeSnippet.id UUIDs
    timestamp: datetime | None = None
    notes: str | None = None


class KillChainCreate(BaseModel):
    name: str
    framework: str = "lockheed"              # lockheed / mitre / custom
    status: str = "active"
    threat_actor_ref: str | None = None
    target_org: str | None = None
    attribution_confidence: float | None = Field(None, ge=0.0, le=1.0)
    description: str | None = None
    objective: str | None = None             # espionage / ransomware / sabotage / fraud
    phases: list[dict[str, Any]] = Field(default_factory=list)
    mitre_techniques: list[str] | None = None
    ioc_refs: list[str] | None = None
    incident_refs: list[str] | None = None
    classification_level: str | None = "UNCLASSIFIED"
    tlp_level: str | None = "AMBER"
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None
    retention_days: int = 0


    created_at: datetime | None = None
class KillChainPhaseUpdate(BaseModel):
    """Payload for adding / updating a single phase."""

    phase: str
    order: int | None = None
    status: str | None = None
    techniques: list[str] | None = None
    tools_used: list[str] | None = None
    ioc_refs: list[str] | None = None
    snippet_refs: list[str] | None = None
    timestamp: datetime | None = None
    notes: str | None = None


class KillChainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    framework: str | None = None
    status: str | None = None
    threat_actor_ref: str | None = None
    target_org: str | None = None
    attribution_confidence: float | None = None
    description: str | None = None
    objective: str | None = None
    phases: list[dict[str, Any]] | None = None
    mitre_techniques: list[str] | None = None
    ioc_refs: list[str] | None = None
    incident_refs: list[str] | None = None
    classification_level: str | None = None
    tlp_level: str | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
