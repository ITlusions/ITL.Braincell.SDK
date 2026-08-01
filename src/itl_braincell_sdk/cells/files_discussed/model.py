"""FileDiscussed SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class FileDiscussed(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "files_discussed"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    language = Column(String, nullable=True)
    purpose = Column(String, nullable=True)
    last_modified = Column(DateTime, nullable=True)
    discussion_count = Column(Integer, default=1)
    meta_data = Column(JSON, nullable=True, default=dict)
