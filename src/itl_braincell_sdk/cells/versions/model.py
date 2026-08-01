"""Versions SQLAlchemy model — version tracking for components."""
import uuid

from sqlalchemy import Column, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class CellVersion(Base, TimestampMixin, RetentionMixin):
    """A recorded version of a component, library, or tool."""

    __tablename__ = "cell_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component = Column(String, nullable=False)         # e.g. "fastapi", "itlc", "postgres"
    version = Column(String, nullable=False)           # e.g. "0.115.2", "2.0.0"
    notes = Column(Text, nullable=True)                # upgrade notes, breaking changes, etc.
    source_interaction_id = Column(UUID(as_uuid=True), nullable=True)
    tags = Column(JSONB, nullable=True, default=list)
    meta_data = Column(JSONB, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_cell_versions_component", "component"),
        Index("ix_cell_versions_source_interaction_id", "source_interaction_id"),
    )
