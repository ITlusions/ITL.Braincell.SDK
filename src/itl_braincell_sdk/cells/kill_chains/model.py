"""KillChain SQLAlchemy model — tracks multi-phase attack campaigns (Lockheed / MITRE ATT&CK)."""
import uuid
from sqlalchemy import Column, String, Float, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSON

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class KillChain(Base, TimestampMixin, RetentionMixin):
    """A kill chain represents an end-to-end attack campaign with ordered phases.

    Each phase records which techniques, tools, and IOCs were active during that
    stage of the attack — enabling campaign-level threat analysis across the full
    Lockheed Martin 7-phase model or MITRE ATT&CK tactic chain.

    Phases JSONB structure:
    [
        {
            "phase": "reconnaissance",       # Lockheed name OR MITRE tactic ID e.g. "TA0043"
            "order": 1,                      # sequential ordering
            "status": "completed",           # completed / active / planned / skipped
            "techniques": ["T1595.002"],     # MITRE ATT&CK technique IDs
            "tools_used": ["Shodan", "nmap"],
            "ioc_refs": ["192.168.1.1"],     # IOC.value strings
            "snippet_refs": [],              # CodeSnippet.id UUIDs (payloads used)
            "timestamp": "2025-03-01T10:00Z",
            "notes": "SSL cert leak identified"
        }
    ]
    """

    __tablename__ = "kill_chains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Campaign identity
    name              = Column(String, nullable=False)                           # e.g. "Kronos campaign Q1 2025"
    framework         = Column(String, nullable=False, default="lockheed")       # lockheed / mitre / custom
    status            = Column(String, nullable=False, default="active")         # active / completed / attributed / archived

    # Attribution
    threat_actor_ref  = Column(String, nullable=True)                            # ThreatActor.name (loose ref)
    target_org        = Column(String, nullable=True)                            # target organisation or sector
    attribution_confidence = Column(Float, nullable=True)                        # 0.0 – 1.0

    # Narrative context
    description       = Column(Text, nullable=True)
    objective         = Column(String, nullable=True)                            # espionage / ransomware / sabotage / fraud

    # Core data — ordered phase array
    phases            = Column(JSON, nullable=False, default=list)               # see docstring above

    # Aggregated cross-reference fields
    mitre_techniques  = Column(JSON, nullable=True, default=list)                # ["T1595", "T1059.001"] — derived from phases
    ioc_refs          = Column(JSON, nullable=True, default=list)                # aggregated IOC refs across all phases
    incident_refs     = Column(JSON, nullable=True, default=list)               # SecurityIncident.id UUIDs

    # Classification
    classification_level = Column(String, nullable=True, default="UNCLASSIFIED")
    tlp_level            = Column(String, nullable=True, default="AMBER")        # WHITE / GREEN / AMBER / RED

    tags              = Column(JSON, nullable=True, default=list)
    meta_data         = Column(JSON, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_kill_chains_status", "status"),
        Index("ix_kill_chains_framework", "framework"),
        Index("ix_kill_chains_threat_actor_ref", "threat_actor_ref"),
    )
