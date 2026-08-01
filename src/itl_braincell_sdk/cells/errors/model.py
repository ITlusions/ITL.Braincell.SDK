"""Errors SQLAlchemy model — bugs, exceptions, and their resolutions."""
import uuid

from sqlalchemy import Column, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class CellError(Base, TimestampMixin, RetentionMixin):
    """A recorded bug, exception, or crash, with optional resolution."""

    __tablename__ = "cell_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    error_type = Column(String, nullable=True)          # e.g. KeyError, ConnectionRefused
    message = Column(Text, nullable=False)              # Full error message / traceback
    context = Column(Text, nullable=True)               # What was being done when it happened
    resolution = Column(Text, nullable=True)            # How it was solved (filled in later)
    status = Column(String, nullable=False, default="open")  # open / resolved / wont_fix
    source_interaction_id = Column(UUID(as_uuid=True), nullable=True)
    tags = Column(JSONB, nullable=True, default=list)
    meta_data = Column(JSONB, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_cell_errors_status", "status"),
        Index("ix_cell_errors_error_type", "error_type"),
        Index("ix_cell_errors_source_interaction_id", "source_interaction_id"),
    )
