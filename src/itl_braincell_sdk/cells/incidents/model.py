"""SecurityIncident SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class SecurityIncident(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "security_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String, nullable=True, default="medium")     # critical / high / medium / low / info
    status = Column(String, nullable=True, default="open")         # open / investigating / contained / resolved / closed
    attack_vector = Column(String, nullable=True)                  # phishing / exploit / insider / supply-chain / ...
    affected_assets = Column(JSON, nullable=True, default=list)    # hostnames / IPs / services impacted
    mitre_tactics = Column(JSON, nullable=True, default=list)      # ["TA0001", "TA0002"]
    threat_actor_name = Column(String, nullable=True)              # attributed actor (if known)
    classification_level = Column(String, nullable=True, default="UNCLASSIFIED")
    tlp_level = Column(String, nullable=True, default="GREEN")     # WHITE / GREEN / AMBER / RED
    detected_at = Column(DateTime, nullable=True)
    contained_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    ioc_refs = Column(JSON, nullable=True, default=list)           # list of IOC value strings
    timeline = Column(JSON, nullable=True, default=list)           # [{timestamp, event, analyst}]
    tags = Column(JSON, nullable=True, default=list)               # free-form tags
    meta_data = Column(JSON, nullable=True, default=dict)
