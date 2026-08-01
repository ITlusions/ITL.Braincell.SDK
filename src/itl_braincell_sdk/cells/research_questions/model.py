"""Research Questions cell — SQLAlchemy model."""
import uuid

from sqlalchemy import Column, String, Text, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class ResearchQuestion(TimestampMixin, RetentionMixin, Base):
    """A question posed by an end user that requires follow-up research.

    Questions can be auto-detected from interactions (role='user') or
    saved manually. Status tracks the investigation lifecycle.
    """

    __tablename__ = "cell_research_questions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    status = Column(String(50), default="pending")     # pending / investigating / answered / closed
    priority = Column(String(20), default="medium")    # low / medium / high
    context = Column(Text, nullable=True)              # surrounding context / conversation snippet
    answer = Column(Text, nullable=True)               # filled in when answered
    source = Column(String(50), default="auto_detected")  # auto_detected / manual
    source_interaction_id = Column(PG_UUID(as_uuid=True), nullable=True)
    tags = Column(ARRAY(String), default=list)
    meta_data = Column(JSON, default=dict)
