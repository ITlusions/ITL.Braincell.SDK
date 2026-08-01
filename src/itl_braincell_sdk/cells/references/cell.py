"""References memory cell — URLs and external sources."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class ReferencesCell(MemoryCell):
    """Memory cell for URLs and external sources mentioned during sessions."""

    @property
    def name(self) -> str:
        return "references"

    @property
    def prefix(self) -> str:
        return "/api/references"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.references.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.references.model import Reference
        return [Reference]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.references.model import Reference

        @mcp.tool()
        async def reference_save(
            url: str,
            title: str | None = None,
            context: str | None = None,
            category: str = "other",
            tags: list[str] | None = None,
        ) -> dict:
            """Save a URL or external source reference.

            Use when a URL, documentation link, GitHub issue, StackOverflow answer,
            or article is mentioned in conversation. Always save with surrounding
            context so the reference is meaningful when retrieved later.
            category values: documentation / github / stackoverflow / article / other
            """
            if not url:
                return {"error": "url is required"}
            db = SyncSessionLocal()
            try:
                row = Reference(
                    url=url,
                    title=title,
                    context=context,
                    category=category,
                    tags=tags or [],
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return {"success": True, "id": str(row.id), "url": url, "category": category}
            finally:
                db.close()

        @mcp.tool()
        async def reference_search(query: str, limit: int = 10) -> dict:
            """Search saved references by URL, title, or context.

            Use to find previously mentioned links, docs, or sources related
            to a topic. Helps avoid re-searching for things already discovered.
            """
            db = SyncSessionLocal()
            try:
                q = query.lower()
                rows = db.query(Reference).filter(
                    Reference.url.ilike(f"%{q}%") |
                    Reference.title.ilike(f"%{q}%") |
                    Reference.context.ilike(f"%{q}%")
                ).order_by(Reference.created_at.desc()).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "url": r.url, "title": r.title,
                     "category": r.category, "context": r.context}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def reference_list(category: str | None = None, limit: int = 50) -> dict:
            """List saved references, optionally filtered by category.

            Use for a broad overview of all saved links or to see all
            references of a specific type (e.g. all github links).
            """
            db = SyncSessionLocal()
            try:
                query = db.query(Reference)
                if category:
                    query = query.filter(Reference.category == category)
                rows = query.order_by(Reference.created_at.desc()).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "url": r.url, "title": r.title,
                     "category": r.category, "tags": r.tags or []}
                    for r in rows
                ]}
            finally:
                db.close()


cell = ReferencesCell()
