"""CodeSnippet SQLAlchemy model"""
import uuid
from sqlalchemy import Column, String, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class CodeSnippet(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "code_snippets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    code_content = Column(String, nullable=False)
    language = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    tags = Column(JSON, nullable=True, default=list)
    meta_data = Column(JSON, nullable=True, default=dict)
