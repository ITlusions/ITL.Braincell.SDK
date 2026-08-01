"""MemorySession SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class MemorySession(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "memory_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_name = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=True, default="active")
    conversation_ids = Column(JSON, nullable=True, default=list)
    file_ids = Column(JSON, nullable=True, default=list)
    summary = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True, default=dict)
