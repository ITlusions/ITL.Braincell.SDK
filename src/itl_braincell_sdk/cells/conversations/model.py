"""Conversation SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class Conversation(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=True)
    topic = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    meta_data = Column(JSON, nullable=True, default=dict)
