"""Snippets memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class SnippetsCell(MemoryCell):
    """Memory cell for code snippets — stores and searches reusable code samples."""

    @property
    def name(self) -> str:
        return "snippets"

    @property
    def prefix(self) -> str:
        return "/api/snippets"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.snippets.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.snippets.model import CodeSnippet
        return [CodeSnippet]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.snippets.model import CodeSnippet

        @mcp.tool()
        async def snippets_search(query: str, limit: int = 10) -> dict:
            """Search reusable code snippets by title, programming language, or description.

            Use when looking for a previously stored code pattern, configuration template,
            or implementation example. Not for file references — use files_discussed_search.
            Not for architectural patterns without code — use architecture_notes_search.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_code(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived_list = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "title": h.get("title"), "language": h.get("language"), "description": h.get("description"), "tags": h.get("tags") or []}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(CodeSnippet).filter(
                        CodeSnippet.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {"query": query, "count": len(rows) + len(archived_list),
                            "results": [{"id": str(r.id), "title": r.title, "language": r.language, "description": r.description, "tags": r.tags or []} for r in rows],
                            "archived": archived_list}
                q = query.lower()
                rows = db.query(CodeSnippet).filter(
                    CodeSnippet.title.ilike(f"%{q}%") |
                    CodeSnippet.description.ilike(f"%{q}%") |
                    CodeSnippet.language.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "title": r.title, "language": r.language,
                     "description": r.description, "tags": r.tags or []}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def snippets_save(
            title: str,
            code_content: str,
            language: str | None = None,
            description: str | None = None,
            tags: list[str] | None = None,
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Save a reusable code snippet or pattern to memory.

            Use when the user provides code worth keeping for future reference — implementations,
            configuration blocks, scripts, query templates, or recurring patterns.
            Always set the language field. Use tags for categorisation.
            Not for prose or general notes — use notes_save.
            Not for file tracking — use files_discussed_save.
            """
            if not title or not code_content:
                return {"error": "title and code_content are required"}
            from itl_braincell_sdk.services.retention_policy import evaluate as _retention
            retention = _retention("snippets", {"title": title, "code_content": code_content, "language": language or "", "description": description or ""})
            if retention_days is not None:
                retention.retention_days = retention_days
            if retain_reason is not None:
                retention.reason = retain_reason
            if not retention.should_save:
                return {"saved": False, "reason": retention.reason}
            db = SyncSessionLocal()
            try:
                row = CodeSnippet(
                    title=title, code_content=code_content,
                    language=language, description=description,
                    tags=tags or [],
                    retention_days=retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=retention.expires_at,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_code_snippet(
                        str(row.id), title=title,
                        code_content=code_content,
                        language=language or "",
                    )
                except Exception:
                    pass
                return {"success": True, "id": str(row.id), "title": title, "retention_days": retention.retention_days, "retain_reason": retention.reason}
            finally:
                db.close()

        @mcp.tool()
        async def snippets_list(limit: int = 50) -> dict:
            """List stored code snippets, newest first.

            Use to browse available code patterns and implementations.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(CodeSnippet).order_by(
                    CodeSnippet.created_at.desc()
                ).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "title": r.title,
                     "language": r.language, "tags": r.tags or []}
                    for r in rows
                ]}
            finally:
                db.close()


cell = SnippetsCell()
