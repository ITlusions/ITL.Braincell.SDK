"""Notes cell — cell definition.

Registers the cell with the BrainCell framework via ``cell = NotesCell()``.
"""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class NotesCell(MemoryCell):
    """Free-form notes cell.

    Stores titled, tagged notes created by an AI agent or user.
    Useful for capturing quick thoughts, reminders, and research findings
    that do not fit the structured decision/architecture note models.
    """

    @property
    def name(self) -> str:
        return "notes"

    @property
    def prefix(self) -> str:
        return "/api/notes"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.notes.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.notes.model import Note
        return [Note]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.notes.model import Note

        @mcp.tool()
        async def notes_search(query: str, limit: int = 10) -> dict:
            """Search free-form notes by title or content.

            Use when looking for a remembered fact, reminder, todo, or general observation.
            Notes are the catch-all cell for information that doesn't fit a more specific category.
            For code use snippets_search; for decisions use decisions_search.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_notes(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived_list = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "title": h.get("title"), "source": h.get("source"), "tags": h.get("tags") or []}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(Note).filter(
                        Note.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {"query": query, "count": len(rows) + len(archived_list),
                            "results": [{"id": str(r.id), "title": r.title, "source": r.source, "tags": r.tags or []} for r in rows],
                            "archived": archived_list}
                q = query.lower()
                rows = db.query(Note).filter(
                    Note.title.ilike(f"%{q}%") | Note.content.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "title": r.title, "source": r.source,
                     "tags": r.tags or []}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def notes_save(
            title: str,
            content: str,
            tags: list[str] | None = None,
            source: str = "agent",
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Save a free-form note to memory.

            Use for reminders, todos, observations, links, or any information that doesn't
            fit a more specific category. This is the default catch-all cell.
            For reusable code use snippets_save.
            For technical choices use decisions_save.
            For component docs use architecture_notes_save.
            """
            if not title or not content:
                return {"error": "title and content are required"}
            from itl_braincell_sdk.services.retention_policy import evaluate as _retention
            retention = _retention("notes", {"title": title, "content": content})
            if retention_days is not None:
                retention.retention_days = retention_days
            if retain_reason is not None:
                retention.reason = retain_reason
            if not retention.should_save:
                return {"saved": False, "reason": retention.reason}
            db = SyncSessionLocal()
            try:
                note = Note(
                    title=title, content=content,
                    tags=tags or [], source=source,
                    retention_days=retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=retention.expires_at,
                )
                db.add(note)
                db.commit()
                db.refresh(note)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_note(
                        str(note.id), title=title,
                        content=content, tags=tags, source=source,
                    )
                except Exception:
                    pass
                return {"success": True, "id": str(note.id), "title": title, "retention_days": retention.retention_days, "retain_reason": retention.reason}
            finally:
                db.close()

        @mcp.tool()
        async def notes_list(limit: int = 50) -> dict:
            """List all notes.

            Use to browse stored observations, reminders, and unstructured information.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(Note).order_by(Note.created_at.desc()).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "title": r.title, "tags": r.tags or []}
                    for r in rows
                ]}
            finally:
                db.close()


cell = NotesCell()
