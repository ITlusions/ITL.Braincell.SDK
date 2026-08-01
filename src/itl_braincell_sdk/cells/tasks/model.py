"""Task SQLAlchemy model."""
import uuid

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class Task(Base, TimestampMixin, RetentionMixin):
    """A task, ticket, or backlog item tracked by an agent or team member."""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="open")        # open / in_progress / done / cancelled / blocked
    priority = Column(String, nullable=False, default="medium")    # critical / high / medium / low
    assignee = Column(String, nullable=True)
    project = Column(String, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSONB, nullable=True, default=list)
    meta_data = Column(JSONB, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_project", "project"),
        Index("ix_tasks_assignee", "assignee"),
    )
