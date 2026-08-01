"""VulnReport memory cell — bug bounty / responsible disclosure dossier management.

Each report tracks the full lifecycle of a vulnerability from discovery
through disclosure, including CVSS scoring, PoC references, affected endpoints,
remediation advice, and bounty payout details.

MCP tools: vuln_report_search · vuln_report_save · vuln_report_update_status
"""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class VulnReportsCell(MemoryCell):
    """Memory cell that manages vulnerability reports and bug bounty dossiers.

    Records contain:
    - CVSS v3.1 score and vector
    - OWASP category, CWE references, CVE candidate
    - Affected product/vendor/endpoints
    - Reproduction steps, PoC references, HTTP capture references
    - Disclosure timeline (discovery → report → vendor ack → patch → disclosure)
    - Bounty program details (HackerOne, Bugcrowd, vendor direct)
    - Status workflow: draft → submitted → triaged → accepted → paid / rejected

    MCP tools: vuln_report_search · vuln_report_save · vuln_report_update_status
    """

    @property
    def name(self) -> str:
        return "vuln_reports"

    @property
    def prefix(self) -> str:
        return "/api/vuln-reports"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.vuln_reports.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.vuln_reports.model import VulnReport
        return [VulnReport]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.vuln_reports.model import VulnReport

        @mcp.tool()
        async def vuln_report_search(
            query: str,
            status_filter: str | None = None,
            severity: str | None = None,
            limit: int = 10,
        ) -> dict:
            """Search vulnerability reports by title, summary, vendor, product, or CVE.

            Use when asked:
            - 'Do we have a report for CVE-XXXX-XXXX?'
            - 'What vulnerabilities did we find in <vendor>?'
            - 'Show me all critical accepted reports'
            - 'What is the status of our HackerOne submissions?'

            Optional filters: status_filter (draft/submitted/triaged/accepted/rejected/paid/disclosed),
            severity (critical/high/medium/low/informational).
            Returns title, vendor, product, cvss_score, severity, status, cve_candidate, summary.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_vuln_reports(query, limit=limit * 2)
                except Exception:
                    pass

                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [
                        h["embedding_id"] for h in wv_hits
                        if not h.get("archived") and h.get("embedding_id")
                    ]
                    q = db.query(VulnReport).filter(
                        VulnReport.id.in_([_UUID(i) for i in live_ids])
                    )
                else:
                    from sqlalchemy import or_
                    q = db.query(VulnReport).filter(
                        or_(
                            VulnReport.title.ilike(f"%{query}%"),
                            VulnReport.summary.ilike(f"%{query}%"),
                            VulnReport.vendor.ilike(f"%{query}%"),
                            VulnReport.product.ilike(f"%{query}%"),
                            VulnReport.cve_candidate.ilike(f"%{query}%"),
                        )
                    )

                if status_filter:
                    q = q.filter(VulnReport.status == status_filter)
                if severity:
                    q = q.filter(VulnReport.severity == severity)

                rows = q.order_by(VulnReport.created_at.desc()).limit(limit).all()
                return {
                    "results": [
                        {
                            "id": str(r.id),
                            "title": r.title,
                            "vendor": r.vendor,
                            "product": r.product,
                            "cve_candidate": r.cve_candidate,
                            "owasp_category": r.owasp_category,
                            "cvss_score": r.cvss_score,
                            "severity": r.severity,
                            "status": r.status,
                            "bounty_program": r.bounty_program,
                            "summary": (r.summary or "")[:300],
                        }
                        for r in rows
                    ]
                }
            finally:
                db.close()

        @mcp.tool()
        async def vuln_report_save(
            title: str,
            summary: str,
            severity: str = "high",
            vendor: str | None = None,
            product: str | None = None,
            affected_versions: str | None = None,
            cve_candidate: str | None = None,
            owasp_category: str | None = None,
            cvss_score: float | None = None,
            cvss_vector: str | None = None,
            affected_endpoints: list[str] | None = None,
            remediation: str | None = None,
            bounty_program: str | None = None,
            program_url: str | None = None,
            reproduction_steps: list[dict] | None = None,
            tags: list[str] | None = None,
        ) -> dict:
            """Create a new vulnerability report (bug bounty dossier).

            Use when:
            - Recording a newly discovered vulnerability
            - Documenting a PoC finding before submission
            - Starting a responsible disclosure workflow

            Severity values: critical / high / medium / low / informational.
            OWASP category example: 'A03:2021-Injection'.
            Returns the created report ID.
            """
            db = SyncSessionLocal()
            try:
                from itl_braincell_sdk.cells.vuln_reports.model import VulnReport as _VR
                record = _VR(
                    title=title,
                    summary=summary,
                    severity=severity,
                    vendor=vendor,
                    product=product,
                    affected_versions=affected_versions,
                    cve_candidate=cve_candidate,
                    owasp_category=owasp_category,
                    cvss_score=cvss_score,
                    cvss_vector=cvss_vector,
                    affected_endpoints=affected_endpoints or [],
                    remediation=remediation,
                    bounty_program=bounty_program,
                    program_url=program_url,
                    reproduction_steps=reproduction_steps or [],
                    tags=tags or [],
                    status="draft",
                    tlp_level="RED",
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_vuln_report(
                        embedding_id=str(record.id),
                        title=title,
                        summary=summary,
                        vendor=vendor or "",
                        product=product or "",
                        cve_candidate=cve_candidate or "",
                        owasp_category=owasp_category or "",
                        status="draft",
                        severity=severity,
                    )
                except Exception:
                    pass
                return {"id": str(record.id), "status": "draft", "title": title}
            finally:
                db.close()

        @mcp.tool()
        async def vuln_report_update_status(
            report_id: str,
            new_status: str,
            submission_id: str | None = None,
            payout_amount: float | None = None,
            tlp_level: str | None = None,
        ) -> dict:
            """Advance the status of a vulnerability report.

            Status flow: draft → submitted → triaged → accepted → paid
            Also accepts: rejected / duplicate / disclosed.

            Use when:
            - Submitting a report to HackerOne or Bugcrowd ('submitted')
            - Vendor acknowledged the issue ('triaged')
            - Bounty was accepted ('accepted') — TLP auto-relaxes to AMBER
            - Payout received ('paid') — provide payout_amount in USD
            - Report was rejected or marked duplicate

            Returns updated status.
            """
            from uuid import UUID as _UUID
            db = SyncSessionLocal()
            try:
                record = db.query(VulnReport).filter(
                    VulnReport.id == _UUID(report_id)
                ).first()
                if not record:
                    return {"error": f"VulnReport {report_id} not found"}
                record.status = new_status
                if submission_id:
                    record.submission_id = submission_id
                if payout_amount is not None:
                    record.payout_amount = payout_amount
                if tlp_level:
                    record.tlp_level = tlp_level
                elif new_status in ("accepted", "paid", "disclosed") and record.tlp_level == "RED":
                    record.tlp_level = "AMBER"
                db.commit()
                db.refresh(record)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_vuln_report(
                        embedding_id=str(record.id),
                        title=record.title,
                        summary=record.summary or "",
                        vendor=record.vendor or "",
                        product=record.product or "",
                        cve_candidate=record.cve_candidate or "",
                        owasp_category=record.owasp_category or "",
                        status=new_status,
                        severity=record.severity,
                    )
                except Exception:
                    pass
                return {
                    "id": str(record.id),
                    "status": record.status,
                    "tlp_level": record.tlp_level,
                    "payout_amount": record.payout_amount,
                }
            finally:
                db.close()


cell = VulnReportsCell()
