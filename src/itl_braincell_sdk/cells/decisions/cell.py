"""Decisions memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class DecisionsCell(MemoryCell):
    """Memory cell for design decisions — tracks architectural choices and rationale."""

    @property
    def name(self) -> str:
        return "decisions"

    @property
    def prefix(self) -> str:
        return "/api/decisions"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.decisions.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.decisions.model import DesignDecision
        return [DesignDecision]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.decisions.model import DesignDecision

        @mcp.tool()
        async def decisions_search(query: str, limit: int = 10) -> dict:
            """Search recorded design or architectural decisions by decision text or rationale.

            Use when asking 'did we decide to use X?', 'why did we choose Y?',
            or 'what was decided about Z?'. Searches both the decision and its reasoning.
            For component design documentation use architecture_notes_search.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_decisions(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived_list = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "decision": h.get("decision"), "rationale": h.get("rationale"), "status": h.get("status")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(DesignDecision).filter(
                        DesignDecision.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {"query": query, "count": len(rows) + len(archived_list),
                            "results": [{"id": str(r.id), "decision": r.decision, "rationale": r.rationale, "status": r.status} for r in rows],
                            "archived": archived_list}
                q = query.lower()
                rows = db.query(DesignDecision).filter(
                    DesignDecision.decision.ilike(f"%{q}%") |
                    DesignDecision.rationale.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "decision": r.decision,
                     "rationale": r.rationale, "status": r.status}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def decisions_save(
            decision: str,
            rationale: str | None = None,
            impact: str | None = None,
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Save a design or architectural decision to memory.

            Use when the user says 'we decided to', 'we chose X', 'let's go with Y because Z',
            or makes any technical or architectural choice with an explicit rationale.
            Not for general notes — use notes_save.
            Not for component documentation — use architecture_notes_save.
            Not for code implementations — use snippets_save.
            """
            if not decision:
                return {"error": "decision is required"}
            from itl_braincell_sdk.services.retention_policy import evaluate as _retention
            retention = _retention("decisions", {"decision": decision, "rationale": rationale or "", "impact": impact or ""})
            if retention_days is not None:
                retention.retention_days = retention_days
            if retain_reason is not None:
                retention.reason = retain_reason
            if not retention.should_save:
                return {"saved": False, "reason": retention.reason}
            db = SyncSessionLocal()
            try:
                row = DesignDecision(
                    decision=decision, rationale=rationale,
                    impact=impact, status="active",
                    retention_days=retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=retention.expires_at,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_decision(
                        str(row.id), decision=decision,
                        rationale=rationale or "",
                    )
                except Exception:
                    pass
                return {"success": True, "id": str(row.id), "decision": decision, "retention_days": retention.retention_days, "retain_reason": retention.reason}
            finally:
                db.close()

        @mcp.tool()
        async def decisions_list(limit: int = 50) -> dict:
            """List all recorded design decisions, newest first.

            Use to review what architectural and technical choices have been made.
            For component-level documentation use architecture_notes_list.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(DesignDecision).order_by(
                    DesignDecision.date_made.desc()
                ).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "decision": (r.decision or "")[:100],
                     "status": r.status}
                    for r in rows
                ]}
            finally:
                db.close()


cell = DecisionsCell()
