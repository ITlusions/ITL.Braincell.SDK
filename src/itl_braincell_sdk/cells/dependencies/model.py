"""Dependency SQLAlchemy model."""
import uuid

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class Dependency(Base, TimestampMixin, RetentionMixin):
    """A tracked software dependency — library, package, or module with version and vulnerability status."""

    __tablename__ = "dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)               # e.g. "requests", "lodash", "log4j"
    version = Column(String, nullable=False)            # e.g. "2.28.1"
    ecosystem = Column(String, nullable=True)           # pypi / npm / nuget / maven / cargo / go / gem / ...
    project = Column(String, nullable=True)             # which internal project uses this
    license = Column(String, nullable=True)             # MIT / Apache-2.0 / GPL-3.0 / ...
    status = Column(String, nullable=False, default="ok")  # ok / vulnerable / deprecated / outdated / unknown
    cve_refs = Column(JSONB, nullable=True, default=list)   # ["CVE-2021-44228", ...]
    upgrade_to = Column(String, nullable=True)          # recommended safe version
    notes = Column(Text, nullable=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(JSONB, nullable=True, default=list)
    meta_data = Column(JSONB, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_dependencies_name", "name"),
        Index("ix_dependencies_ecosystem", "ecosystem"),
        Index("ix_dependencies_status", "status"),
        Index("ix_dependencies_project", "project"),
    )
