"""IOC (Indicator of Compromise) SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON, Float, Text
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class IOC(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "iocs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)                          # ip / domain / hash_md5 / hash_sha1 / hash_sha256 / url / email / cve / yara
    value = Column(String, nullable=False, index=True)             # the actual IOC value
    confidence = Column(Float, nullable=True, default=0.5)         # 0.0 - 1.0
    severity = Column(String, nullable=True, default="medium")     # critical / high / medium / low
    status = Column(String, nullable=True, default="active")       # active / expired / false_positive / under_review
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    source = Column(String, nullable=True)                         # OSINT / internal / ISAC / vendor
    tags = Column(JSON, nullable=True, default=list)               # ["ransomware", "c2", "exfil"]
    context = Column(Text, nullable=True)                          # human-readable description
    incident_refs = Column(JSON, nullable=True, default=list)      # incident IDs that referenced this IOC
    threat_actor_refs = Column(JSON, nullable=True, default=list)  # threat actor names attributed to this IOC
    classification_level = Column(String, nullable=True, default="UNCLASSIFIED")
    tlp_level = Column(String, nullable=True, default="GREEN")
    meta_data = Column(JSON, nullable=True, default=dict)
