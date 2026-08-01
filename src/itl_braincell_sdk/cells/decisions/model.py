"""DesignDecision SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class DesignDecision(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "design_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision = Column(String, nullable=True)
    rationale = Column(String, nullable=True)
    impact = Column(String, nullable=True)
    status = Column(String, nullable=True, default="active")
    date_made = Column(DateTime, nullable=True)
    meta_data = Column(JSON, nullable=True, default=dict)
