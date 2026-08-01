"""VulnReport SQLAlchemy model — full bug bounty / responsible disclosure dossier.

Covers the full lifecycle from discovery → submission → triage → payout,
structured to match HackerOne / Bugcrowd / vendor-direct report formats.
Each report ties together: PoC code (snippets), HTTP captures (files_discussed),
IOCs (affected endpoints), CVSS scoring, and disclosure timeline.
"""
import uuid
from sqlalchemy import Column, String, Float, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSON

from itl_braincell_sdk.core.models import Base, TimestampMixin, RetentionMixin


class VulnReport(Base, TimestampMixin, RetentionMixin):
    """A vulnerability report / bug bounty dossier.

    Disclosure timeline JSON structure:
    {
        "discovered_at": "2025-03-01T10:00Z",
        "reported_at":   "2025-03-03T09:00Z",
        "vendor_acknowledged_at": "2025-03-05T14:00Z",
        "patch_expected_at": "2025-06-01T00:00Z",
        "patched_at": "2025-05-20T00:00Z",
        "public_disclosure_at": "2025-06-20T00:00Z",   # 90-day rule
        "cve_assigned_at": "2025-04-01T00:00Z"
    }

    Reproduction steps JSON structure:
    [
        {
            "step": 1,
            "action": "Send HTTP request to /api/users?id=1 OR 1=1--",
            "expected": "400 Bad Request",
            "actual": "200 OK with full user table dump"
        }
    ]

    Affected artifacts JSON structure:
    [
        {
            "product": "ExampleApp",
            "version": "3.4.1",
            "sha256": "abc123...",
            "download_url": "https://vendor.com/download/3.4.1",
            "platform": "linux-amd64"
        }
    ]
    """

    __tablename__ = "vuln_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Report identity
    title                = Column(String, nullable=False)
    internal_id          = Column(String, nullable=True)                   # e.g. "ITL-2025-001"
    cve_candidate        = Column(String, nullable=True)                   # e.g. "CVE-2025-12345"
    cwe_refs             = Column(JSON, nullable=True, default=list)       # ["CWE-89", "CWE-79"]
    owasp_category       = Column(String, nullable=True)                   # "A03:2021-Injection"

    # Target
    vendor               = Column(String, nullable=True)
    product              = Column(String, nullable=True)
    affected_versions    = Column(String, nullable=True)                   # "< 3.4.2"
    affected_endpoints   = Column(JSON, nullable=True, default=list)       # ["https://app.com/api/users"]

    # CVSS v3.1
    cvss_score           = Column(Float, nullable=True)                    # 0.0 – 10.0
    cvss_vector          = Column(String, nullable=True)                   # "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    attack_vector        = Column(String, nullable=True)                   # network / adjacent / local / physical
    privileges_required  = Column(String, nullable=True)                   # none / low / high
    user_interaction     = Column(String, nullable=True)                   # none / required
    impact_confidentiality = Column(String, nullable=True)                 # none / low / high
    impact_integrity     = Column(String, nullable=True)
    impact_availability  = Column(String, nullable=True)

    # Narrative
    summary              = Column(Text, nullable=True)                     # short executive summary
    technical_details    = Column(Text, nullable=True)                     # deep technical description
    impact_description   = Column(Text, nullable=True)                     # what an attacker can do
    remediation          = Column(Text, nullable=True)                     # recommended fix

    # PoC references (cross-cell)
    poc_snippet_refs     = Column(JSON, nullable=True, default=list)       # snippets.id UUIDs
    capture_refs         = Column(JSON, nullable=True, default=list)       # files_discussed.id UUIDs (Burp/curl captures)
    ioc_refs             = Column(JSON, nullable=True, default=list)       # iocs.id UUIDs (affected hosts, hashes)
    vuln_patch_refs      = Column(JSON, nullable=True, default=list)       # vuln_patches.id UUIDs

    # Reproduction
    environment          = Column(String, nullable=True)                   # "Ubuntu 22.04, Chrome 124"
    prerequisites        = Column(Text, nullable=True)                     # "Valid user account required"
    reproduction_steps   = Column(JSON, nullable=True, default=list)      # see docstring above
    affected_artifacts   = Column(JSON, nullable=True, default=list)       # see docstring above

    # Disclosure & bounty
    disclosure_timeline  = Column(JSON, nullable=True, default=dict)      # see docstring above
    bounty_program       = Column(String, nullable=True)                   # "HackerOne" / "Bugcrowd" / "vendor-direct"
    program_url          = Column(String, nullable=True)                   # bounty program URL
    submission_id        = Column(String, nullable=True)                   # platform report ID
    payout_amount        = Column(Float, nullable=True)                    # USD
    payout_currency      = Column(String, nullable=True, default="USD")

    # Status
    status               = Column(String, nullable=False, default="draft") # draft / submitted / triaged / accepted / rejected / duplicate / paid / disclosed
    severity             = Column(String, nullable=False, default="high")  # critical / high / medium / low / informational
    classification_level = Column(String, nullable=True, default="UNCLASSIFIED")
    tlp_level            = Column(String, nullable=True, default="RED")    # default RED until accepted

    tags                 = Column(JSON, nullable=True, default=list)
    meta_data            = Column(JSON, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_vuln_reports_status", "status"),
        Index("ix_vuln_reports_severity", "severity"),
        Index("ix_vuln_reports_vendor", "vendor"),
        Index("ix_vuln_reports_cve_candidate", "cve_candidate"),
    )
