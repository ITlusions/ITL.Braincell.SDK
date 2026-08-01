"""Persons SQLAlchemy model — people and roles."""
import uuid

from sqlalchemy import Column, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class Person(Base, TimestampMixin, RetentionMixin):
    """A person, their role, and contact/team details."""

    __tablename__ = "persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    responsibilities = Column(JSONB, nullable=True, default=list)  # list[str]
    contact_info = Column(Text, nullable=True)
    team = Column(String, nullable=True)
    source_interaction_id = Column(UUID(as_uuid=True), nullable=True)
    tags = Column(JSONB, nullable=True, default=list)
    meta_data = Column(JSONB, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_persons_name", "name"),
        Index("ix_persons_team", "team"),
        Index("ix_persons_source_interaction_id", "source_interaction_id"),
    )
