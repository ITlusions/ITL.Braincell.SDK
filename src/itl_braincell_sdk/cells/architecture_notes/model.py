"""ArchitectureNote SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class ArchitectureNote(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "architecture_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component = Column(String, nullable=True)
    description = Column(String, nullable=True)
    type = Column(String, nullable=True)
    status = Column(String, nullable=True, default="active")
    tags = Column(JSON, nullable=True, default=list)
    meta_data = Column(JSON, nullable=True, default=dict)
