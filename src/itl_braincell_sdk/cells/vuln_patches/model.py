"""VulnPatch SQLAlchemy model — stores known vulnerable code alongside its patched equivalent."""
import uuid
from sqlalchemy import Column, String, Text, JSON, Float, Index
from sqlalchemy.dialects.postgresql import UUID

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class VulnPatch(Base, TimestampMixin, RetentionMixin):
    __tablename__ = "vuln_patches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    language = Column(String, nullable=True)                        # python / javascript / c / java / go / ...
    category = Column(String, nullable=True)                        # sql_injection / xss / buffer_overflow / path_traversal / ...

    severity = Column(String, nullable=False, default="high")       # critical / high / medium / low
    confidence_score = Column(Float, nullable=True, default=1.0)   # how certain is the classification (0-1)

    vulnerable_code = Column(Text, nullable=False)                  # the vulnerable snippet
    patched_code = Column(Text, nullable=False)                     # the fixed version
    patch_explanation = Column(Text, nullable=True)                 # human-readable explanation of what changed and why

    cve_refs = Column(JSON, nullable=True, default=list)            # ["CVE-2021-44228", ...]
    cwe_refs = Column(JSON, nullable=True, default=list)            # ["CWE-89", ...]     (weakness IDs)
    owasp_refs = Column(JSON, nullable=True, default=list)          # ["A03:2021"]

    source = Column(String, nullable=True)                          # nvd / internal / osv / manual / ...
    tags = Column(JSON, nullable=True, default=list)
    meta_data = Column(JSON, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_vuln_patches_language", "language"),
        Index("ix_vuln_patches_severity", "severity"),
        Index("ix_vuln_patches_category", "category"),
    )
