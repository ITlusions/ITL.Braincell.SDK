"""ApiContract SQLAlchemy model."""
import uuid

from sqlalchemy import Column, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class ApiContract(Base, TimestampMixin, RetentionMixin):
    """An API contract — the specification, versioning, and changelog of an internal or external API."""

    __tablename__ = "api_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    service_name = Column(String, nullable=False)      # e.g. "ITL Control Plane API"
    version = Column(String, nullable=False)           # e.g. "v2.1.0"
    base_url = Column(String, nullable=True)           # e.g. "https://api.itlusions.com/v2"
    spec_format = Column(String, nullable=True)        # openapi / graphql / grpc / rest / soap
    spec_content = Column(Text, nullable=True)         # Full spec, or summary/extract
    status = Column(String, nullable=False, default="active")  # active / deprecated / draft / sunset
    breaking_changes = Column(Text, nullable=True)
    changelog = Column(JSONB, nullable=True, default=list)  # [{version, date, summary, breaking}]
    endpoints = Column(JSONB, nullable=True, default=list)   # [{method, path, summary, deprecated}]
    auth_type = Column(String, nullable=True)          # bearer / apikey / oauth2 / none
    tags = Column(JSONB, nullable=True, default=list)
    meta_data = Column(JSONB, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_api_contracts_service_name", "service_name"),
        Index("ix_api_contracts_version", "version"),
        Index("ix_api_contracts_status", "status"),
    )
