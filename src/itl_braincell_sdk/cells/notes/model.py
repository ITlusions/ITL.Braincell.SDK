"""Notes cell — SQLAlchemy model."""
import uuid

from sqlalchemy import Column, String, Text, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class Note(TimestampMixin, RetentionMixin, Base):
    """Free-form note with optional tags — managed by the notes cell."""

    __tablename__ = "cell_notes"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(String), default=list)
    source = Column(String(255), default="manual")
    meta_data = Column(JSON, default=dict)
