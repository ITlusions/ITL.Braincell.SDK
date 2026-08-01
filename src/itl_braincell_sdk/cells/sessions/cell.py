"""Sessions memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class SessionsCell(MemoryCell):
    """Memory cell for memory sessions — manages conversation context windows."""

    @property
    def name(self) -> str:
        return "sessions"

    @property
    def prefix(self) -> str:
        return "/api/sessions"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.sessions.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.sessions.model import MemorySession
        return [MemorySession]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.sessions.model import MemorySession

        @mcp.tool()
        async def sessions_search(query: str, limit: int = 10) -> dict:
            """Search past work sessions by session name or summary.

            Use when looking for what was accomplished in a previous coding session,
            what state a feature was left in, or what the next steps were.
            For individual messages from a session use interactions_search.
            For conversation topics use conversations_search.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_sessions(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived_list = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "session_name": h.get("session_name"), "status": h.get("status"), "summary": h.get("summary")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(MemorySession).filter(
                        MemorySession.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {"query": query, "count": len(rows) + len(archived_list),
                            "results": [{"id": str(r.id), "session_name": r.session_name, "status": r.status, "summary": r.summary} for r in rows],
                            "archived": archived_list}
                q = query.lower()
                rows = db.query(MemorySession).filter(
                    MemorySession.session_name.ilike(f"%{q}%") |
                    MemorySession.summary.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "session_name": r.session_name,
                     "status": r.status, "summary": r.summary}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def sessions_save(
            session_name: str,
            summary: str | None = None,
            status: str = "active",
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Save a work session summary to memory.

            Use at the start or end of a coding session to record what was worked on,
            the current status, and what comes next. status should be one of:
            'active' (session is in progress), 'completed', or 'paused'.
            Not for individual messages — use interactions_save.
            Not for conversation summaries — use conversations_save.
            """
            if not session_name:
                return {"error": "session_name is required"}
            from datetime import datetime, timezone
            from itl_braincell_sdk.services.retention_policy import evaluate as _retention
            retention = _retention("sessions", {"session_name": session_name, "summary": summary or ""})
            if retention_days is not None:
                retention.retention_days = retention_days
            if retain_reason is not None:
                retention.reason = retain_reason
            if not retention.should_save:
                return {"saved": False, "reason": retention.reason}
            db = SyncSessionLocal()
            try:
                row = MemorySession(
                    session_name=session_name, summary=summary,
                    status=status, start_time=datetime.now(timezone.utc),
                    retention_days=retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=retention.expires_at,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_memory_session(
                        str(row.id), session_name=session_name,
                        summary=summary or "",
                        status=status,
                    )
                except Exception:
                    pass
                return {"success": True, "id": str(row.id), "session_name": session_name, "retention_days": retention.retention_days, "retain_reason": retention.reason}
            finally:
                db.close()

        @mcp.tool()
        async def sessions_list(limit: int = 50) -> dict:
            """List work sessions, most recent first.

            Use to see a history of coding sessions and review their status and summaries.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(MemorySession).order_by(
                    MemorySession.start_time.desc()
                ).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "session_name": r.session_name,
                     "status": r.status}
                    for r in rows
                ]}
            finally:
                db.close()


cell = SessionsCell()
