"""IntelReport SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON, Float, Text
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class IntelReport(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "intel_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)                           # full report body (Markdown)
    classification_level = Column(String, nullable=True, default="UNCLASSIFIED")
    tlp_level = Column(String, nullable=True, default="GREEN")      # WHITE / GREEN / AMBER / RED
    source = Column(String, nullable=True)                          # OSINT / HUMINT / SIGINT / internal
    analyst = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True, default=0.5)   # 0.0 - 1.0
    report_date = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    tags = Column(JSON, nullable=True, default=list)                # ["apt", "ransomware", "zero-day"]
    ioc_refs = Column(JSON, nullable=True, default=list)            # IOC values referenced in report
    threat_actor_refs = Column(JSON, nullable=True, default=list)   # threat actor names referenced
    incident_refs = Column(JSON, nullable=True, default=list)       # incident IDs referenced
    mitre_techniques = Column(JSON, nullable=True, default=list)    # ["T1566", "T1059"]
    meta_data = Column(JSON, nullable=True, default=dict)
