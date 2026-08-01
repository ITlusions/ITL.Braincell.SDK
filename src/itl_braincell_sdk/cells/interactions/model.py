"""Interaction SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class Interaction(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    session_id = Column(UUID(as_uuid=True), nullable=True)
    role = Column(String, nullable=True)
    content = Column(String, nullable=True)
    message_type = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    meta_data = Column(JSON, nullable=True, default=dict)
