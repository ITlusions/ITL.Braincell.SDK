"""Runbook SQLAlchemy model."""
import uuid

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class Runbook(Base, TimestampMixin, RetentionMixin):
    """An operational runbook — step-by-step procedure for deployments, incidents, maintenance."""

    __tablename__ = "runbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)           # incident_response / deployment / maintenance / onboarding / backup / rollback / ...
    trigger = Column(Text, nullable=True)              # When should this runbook be used?
    prerequisites = Column(Text, nullable=True)        # What must be true before starting?
    steps = Column(JSONB, nullable=False, default=list)  # [{step, title, command, expected_output, notes}]
    rollback_steps = Column(JSONB, nullable=True, default=list)  # steps to undo
    severity = Column(String, nullable=True)           # for incident runbooks: P1/P2/P3
    services = Column(JSONB, nullable=True, default=list)  # affected service names
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSONB, nullable=True, default=list)
    meta_data = Column(JSONB, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_runbooks_category", "category"),
        Index("ix_runbooks_severity", "severity"),
    )
