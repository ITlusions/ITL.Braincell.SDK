"""Files discussed memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class FilesDiscussedCell(MemoryCell):
    """Memory cell for files discussed — tracks files referenced in conversations."""

    @property
    def name(self) -> str:
        return "files_discussed"

    @property
    def prefix(self) -> str:
        return "/api/files"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.files_discussed.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.files_discussed.model import FileDiscussed
        return [FileDiscussed]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.files_discussed.model import FileDiscussed

        @mcp.tool()
        async def files_discussed_search(query: str, limit: int = 10) -> dict:
            """Search for files that have been discussed, by path, description, or purpose.

            Use when you want to know if a specific file has been referenced before,
            what it was used for, or how often it came up in past sessions.
            For code content stored from a file use snippets_search.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_files(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived_list = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "file_path": h.get("file_path"), "language": h.get("language"), "purpose": h.get("purpose"), "discussion_count": h.get("discussion_count")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(FileDiscussed).filter(
                        FileDiscussed.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {"query": query, "count": len(rows) + len(archived_list),
                            "results": [{"id": str(r.id), "file_path": r.file_path, "language": r.language, "purpose": r.purpose, "discussion_count": r.discussion_count} for r in rows],
                            "archived": archived_list}
                q = query.lower()
                rows = db.query(FileDiscussed).filter(
                    FileDiscussed.file_path.ilike(f"%{q}%") |
                    FileDiscussed.description.ilike(f"%{q}%") |
                    FileDiscussed.purpose.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "file_path": r.file_path,
                     "language": r.language, "purpose": r.purpose,
                     "discussion_count": r.discussion_count}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def files_discussed_save(
            file_path: str,
            description: str | None = None,
            language: str | None = None,
            purpose: str | None = None,
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Record that a file was discussed or referenced in a session.

            Use when a file is mentioned, reviewed, edited, or created during a conversation.
            Automatically increments the discussion count if the file was already recorded,
            so calling this multiple times for the same file is safe and intentional.
            Not for storing code content — use snippets_save.
            """
            if not file_path:
                return {"error": "file_path is required"}
            from itl_braincell_sdk.services.retention_policy import evaluate as _retention
            retention = _retention("files_discussed", {"file_path": file_path, "description": description or "", "purpose": purpose or ""})
            if retention_days is not None:
                retention.retention_days = retention_days
            if retain_reason is not None:
                retention.reason = retain_reason
            if not retention.should_save:
                return {"saved": False, "reason": retention.reason}
            db = SyncSessionLocal()
            try:
                existing = db.query(FileDiscussed).filter(
                    FileDiscussed.file_path == file_path
                ).first()
                if existing:
                    existing.discussion_count = (existing.discussion_count or 0) + 1
                    if description:
                        existing.description = description
                    db.commit()
                    try:
                        from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                        _gwvs().index_file_discussed(
                            str(existing.id),
                            file_path=file_path,
                            description=description or "",
                            language=language or "",
                            purpose=purpose or "",
                        )
                    except Exception:
                        pass
                    return {"success": True, "id": str(existing.id),
                            "discussion_count": existing.discussion_count}
                row = FileDiscussed(
                    file_path=file_path, description=description,
                    language=language, purpose=purpose,
                    retention_days=retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=retention.expires_at,
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_file_discussed(
                        str(row.id), file_path=file_path,
                        description=description or "",
                        language=language or "",
                        purpose=purpose or "",
                    )
                except Exception:
                    pass
                return {"success": True, "id": str(row.id), "file_path": file_path, "retention_days": retention.retention_days, "retain_reason": retention.reason}
            finally:
                db.close()

        @mcp.tool()
        async def files_discussed_list(limit: int = 50) -> dict:
            """List files discussed, ordered by how often they were referenced.

            Use to see which files have been most frequently worked on or mentioned.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(FileDiscussed).order_by(
                    FileDiscussed.discussion_count.desc()
                ).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "file_path": r.file_path,
                     "language": r.language, "discussion_count": r.discussion_count}
                    for r in rows
                ]}
            finally:
                db.close()


cell = FilesDiscussedCell()
