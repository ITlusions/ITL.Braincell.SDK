from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at / updated_at timestamp fields"""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class RetentionMixin:
    """Mixin that records retention metadata on every stored row.

    Fields
    ------
    retention_days  : 0 = keep forever; > 0 = expire after N days from created_at.
    retain_reason   : Human-readable explanation of why (or why not) this was kept.
    expires_at      : UTC timestamp when the row should be purged (NULL = never).
    """

    @declared_attr
    def retention_days(cls):
        return Column(Integer, nullable=False, default=0)

    @declared_attr
    def retain_reason(cls):
        return Column(String(500), nullable=True)

    @declared_attr
    def expires_at(cls):
        return Column(DateTime(timezone=True), nullable=True)


# Entity models have moved to itl_braincell_sdk/cells/<name>/model.py
