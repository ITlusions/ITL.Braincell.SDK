"""ThreatActor SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON, Float
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class ThreatActor(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "threat_actors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    aliases = Column(JSON, nullable=True, default=list)           # ["APT28", "Fancy Bear"]
    classification = Column(String, nullable=True)                # apt / criminal / hacktivist / state-sponsored / unknown
    origin_country = Column(String, nullable=True)
    motivation = Column(String, nullable=True)                    # espionage / financial / disruption / ideological
    sophistication = Column(String, nullable=True)                # low / medium / high / nation-state
    ttps = Column(JSON, nullable=True, default=list)              # ["T1566", "T1059.001"]  (MITRE ATT&CK IDs)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    status = Column(String, nullable=True, default="active")      # active / inactive / unknown
    confidence_score = Column(Float, nullable=True, default=0.5)  # 0.0 - 1.0
    stix_id = Column(String, nullable=True)                       # STIX 2.1 identity
    meta_data = Column(JSON, nullable=True, default=dict)
