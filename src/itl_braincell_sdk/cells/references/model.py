"""References SQLAlchemy model — URLs and external sources."""
import uuid

from sqlalchemy import Column, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class Reference(Base, TimestampMixin, RetentionMixin):
    """A URL or external source mentioned during a session."""

    __tablename__ = "cell_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)
    title = Column(String, nullable=True)
    # Sentence or paragraph surrounding the URL when it was mentioned
    context = Column(Text, nullable=True)
    category = Column(String, nullable=False, default="other")  # documentation / github / stackoverflow / article / other
    source_interaction_id = Column(UUID(as_uuid=True), nullable=True)
    tags = Column(JSONB, nullable=True, default=list)
    meta_data = Column(JSONB, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_cell_references_category", "category"),
        Index("ix_cell_references_source_interaction_id", "source_interaction_id"),
    )
