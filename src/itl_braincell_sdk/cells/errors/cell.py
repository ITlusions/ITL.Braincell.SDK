"""Errors memory cell — bugs, exceptions, and their resolutions."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class ErrorsCell(MemoryCell):
    """Memory cell for recorded errors, exceptions, and their resolutions."""

    @property
    def name(self) -> str:
        return "errors"

    @property
    def prefix(self) -> str:
        return "/api/errors"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.errors.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.errors.model import CellError
        return [CellError]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.errors.model import CellError

        @mcp.tool()
        async def error_save(
            message: str,
            error_type: str | None = None,
            context: str | None = None,
            tags: list[str] | None = None,
        ) -> dict:
            """Record an error, exception, bug, or crash for memory.

            Auto-trigger on: Traceback lines, Error:/Exception:/FATAL: prefixes,
            or messages containing error/exception/crash/bug keywords.
            error_type is the class name (e.g. KeyError, ConnectionRefusedError).
            context describes what was being attempted when the error occurred.
            """
            if not message:
                return {"error": "message is required"}
            db = SyncSessionLocal()
            try:
                row = CellError(
                    message=message,
                    error_type=error_type,
                    context=context,
                    tags=tags or [],
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return {"success": True, "id": str(row.id), "status": row.status}
            finally:
                db.close()

        @mcp.tool()
        async def error_resolve(error_id: str, resolution: str) -> dict:
            """Mark a previously recorded error as resolved, storing how it was fixed.

            Use whenever a solution is found for a previously logged error.
            resolution should concisely explain what the fix was.
            """
            import uuid as _uuid
            db = SyncSessionLocal()
            try:
                row = db.query(CellError).filter(CellError.id == _uuid.UUID(error_id)).first()
                if not row:
                    return {"error": f"Error {error_id} not found"}
                row.status = "resolved"
                row.resolution = resolution
                db.commit()
                db.refresh(row)
                return {"success": True, "id": error_id, "status": "resolved"}
            finally:
                db.close()

        @mcp.tool()
        async def error_search(query: str, limit: int = 10) -> dict:
            """Search recorded errors by type, message, or context.

            Use to check whether a similar error has occurred before and whether
            it was already resolved. Helps avoid re-investigating known issues.
            """
            db = SyncSessionLocal()
            try:
                q = query.lower()
                rows = db.query(CellError).filter(
                    CellError.message.ilike(f"%{q}%") |
                    CellError.error_type.ilike(f"%{q}%") |
                    CellError.context.ilike(f"%{q}%") |
                    CellError.resolution.ilike(f"%{q}%")
                ).order_by(CellError.created_at.desc()).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "error_type": r.error_type, "message": r.message[:200],
                     "status": r.status, "resolution": r.resolution}
                    for r in rows
                ]}
            finally:
                db.close()


cell = ErrorsCell()
