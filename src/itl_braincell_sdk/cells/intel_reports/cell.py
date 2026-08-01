"""Intel Reports memory cell — structured intelligence analysis and threat briefings."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class IntelReportsCell(MemoryCell):
    """Memory cell for threat intelligence reports — TLP-marked, MITRE-referenced analysis."""

    @property
    def name(self) -> str:
        return "intel_reports"

    @property
    def prefix(self) -> str:
        return "/api/intel_reports"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.intel_reports.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.intel_reports.model import IntelReport
        return [IntelReport]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.intel_reports.model import IntelReport

        @mcp.tool()
        async def intel_reports_search(query: str, limit: int = 10) -> dict:
            """Search threat intelligence reports by title, summary, tags, or MITRE techniques.

            Use when asked 'what do we know about this threat?', 'is there a report on this campaign?',
            'show me recent intelligence about ransomware', or 'find reports referencing APT29'.
            Returns reports with classification level, TLP marking, and referenced IOCs.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_intel_reports(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "title": h.get("title"), "classification_level": h.get("classification_level")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(IntelReport).filter(
                        IntelReport.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {
                        "query": query, "count": len(rows) + len(archived),
                        "results": [
                            {"id": str(r.id), "title": r.title, "summary": r.summary,
                             "classification_level": r.classification_level, "tlp_level": r.tlp_level,
                             "source": r.source, "analyst": r.analyst, "confidence_score": r.confidence_score,
                             "tags": r.tags, "ioc_refs": r.ioc_refs, "threat_actor_refs": r.threat_actor_refs,
                             "mitre_techniques": r.mitre_techniques,
                             "report_date": r.report_date.isoformat() if r.report_date else None}
                            for r in rows
                        ],
                        "archived": archived,
                    }
                q = query.lower()
                rows = db.query(IntelReport).filter(
                    IntelReport.title.ilike(f"%{q}%") |
                    IntelReport.summary.ilike(f"%{q}%") |
                    IntelReport.content.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "title": r.title, "summary": r.summary,
                     "classification_level": r.classification_level, "tlp_level": r.tlp_level,
                     "source": r.source, "analyst": r.analyst,
                     "report_date": r.report_date.isoformat() if r.report_date else None}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def intel_reports_save(
            title: str,
            summary: str | None = None,
            content: str | None = None,
            classification_level: str = "UNCLASSIFIED",
            tlp_level: str = "GREEN",
            source: str | None = None,
            analyst: str | None = None,
            confidence_score: float = 0.5,
            tags: list[str] | None = None,
            ioc_refs: list[str] | None = None,
            threat_actor_refs: list[str] | None = None,
            mitre_techniques: list[str] | None = None,
            retention_days: int | None = None,
        ) -> dict:
            """Save a threat intelligence report to BrainCell memory.

            Use when producing or receiving structured threat intelligence:
            threat briefings, incident summaries, campaign analysis, or OSINT reports.
            classification_level: UNCLASSIFIED / SENSITIVE / CONFIDENTIAL / SECRET
            tlp_level: WHITE / GREEN / AMBER / RED
            source: OSINT / HUMINT / SIGINT / ISAC / internal
            ioc_refs: IOC values referenced in the report
            threat_actor_refs: threat actor names discussed
            mitre_techniques: MITRE ATT&CK technique IDs used in the report
            """
            from datetime import datetime, timezone
            db = SyncSessionLocal()
            try:
                from itl_braincell_sdk.cells.intel_reports.model import IntelReport as _IR
                report = _IR(
                    title=title,
                    summary=summary,
                    content=content,
                    classification_level=classification_level,
                    tlp_level=tlp_level,
                    source=source,
                    analyst=analyst,
                    confidence_score=confidence_score,
                    tags=tags or [],
                    ioc_refs=ioc_refs or [],
                    threat_actor_refs=threat_actor_refs or [],
                    mitre_techniques=mitre_techniques or [],
                    report_date=datetime.now(timezone.utc),
                )
                if retention_days is not None:
                    report.retention_days = retention_days
                db.add(report)
                db.commit()
                db.refresh(report)

                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_intel_report(str(report.id), title, summary, content)
                except Exception:
                    pass

                return {
                    "status": "saved", "id": str(report.id), "title": report.title,
                    "classification_level": report.classification_level, "tlp_level": report.tlp_level,
                }
            finally:
                db.close()


cell = IntelReportsCell()
