"""Architecture notes memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class ArchitectureNotesCell(MemoryCell):
    """Memory cell for architecture notes — documents system components and patterns."""

    @property
    def name(self) -> str:
        return "architecture_notes"

    @property
    def prefix(self) -> str:
        return "/api/architecture-notes"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.architecture_notes.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.architecture_notes.model import ArchitectureNote
        return [ArchitectureNote]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.architecture_notes.model import ArchitectureNote

        @mcp.tool()
        async def architecture_notes_search(query: str, limit: int = 10) -> dict:
            """Search architecture notes by component name or description.

            Use when looking for how a system component is designed, its purpose,
            or its relationship to other components. Prefer over decisions_search when
            the query is about system structure or component design rather than a
            specific technical choice.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_architecture_notes(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived_list = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "component": h.get("component"), "description": h.get("description"), "type": h.get("note_type")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(ArchitectureNote).filter(
                        ArchitectureNote.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {"query": query, "count": len(rows) + len(archived_list),
                            "results": [{"id": str(r.id), "component": r.component, "description": (r.description or "")[:200], "type": r.type} for r in rows],
                            "archived": archived_list}
                q = query.lower()
                rows = db.query(ArchitectureNote).filter(
                    ArchitectureNote.component.ilike(f"%{q}%") |
                    ArchitectureNote.description.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "component": r.component,
                     "description": (r.description or "")[:200], "type": r.type}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def architecture_notes_save(
            component: str,
            description: str,
            note_type: str | None = None,
            tags: list[str] | None = None,
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Save an architecture or design note about a system component.

            Use when documenting how a component works, its role in the system,
            its design patterns, or its relationships. Covers services, modules,
            APIs, databases, and infrastructure components.
            Not for specific technical choices — use decisions_save.
            Not for code implementations — use snippets_save.
            """
            if not component or not description:
                return {"error": "component and description are required"}
            from itl_braincell_sdk.services.retention_policy import evaluate as _retention
            retention = _retention("architecture_notes", {"component": component, "description": description})
            if retention_days is not None:
                retention.retention_days = retention_days
            if retain_reason is not None:
                retention.reason = retain_reason
            if not retention.should_save:
                return {"saved": False, "reason": retention.reason}
            db = SyncSessionLocal()
            try:
                row = ArchitectureNote(
                    component=component, description=description,
                    type=note_type or "general", tags=tags or [], status="active",
                    retention_days=retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=retention.expires_at,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_architecture_note(
                        str(row.id), component=component,
                        description=description or "",
                        note_type=note_type,
                        tags=tags,
                    )
                except Exception:
                    pass
                return {"success": True, "id": str(row.id), "component": component, "retention_days": retention.retention_days, "retain_reason": retention.reason}
            finally:
                db.close()

        @mcp.tool()
        async def architecture_notes_list(limit: int = 50) -> dict:
            """List architecture notes sorted alphabetically by component name.

            Use to see what system components are documented.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(ArchitectureNote).order_by(
                    ArchitectureNote.component
                ).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "component": r.component,
                     "description": (r.description or "")[:100]}
                    for r in rows
                ]}
            finally:
                db.close()


cell = ArchitectureNotesCell()
