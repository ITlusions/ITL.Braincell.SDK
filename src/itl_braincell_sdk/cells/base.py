"""BrainCell — MemoryCell plugin interface.

A MemoryCell is a self-contained memory domain. Creating a new cell requires only:
  1. A directory under src/cells/<name>/
  2. A cell.py that exports a `cell` object (instance of MemoryCell)
  3. Optionally: model.py, schema.py, routes.py — all private to the cell

The core framework auto-discovers and registers every cell at startup."""
from abc import ABC, abstractmethod
from typing import Any

from fastapi import APIRouter
from sqlalchemy.orm import Session


class MemoryCell(ABC):
    """Abstract base for all BrainCell memory cells.

    Subclass this and export an instance named ``cell`` from your cell module.

    Minimal implementation example::

        class MyCell(MemoryCell):
            @property
            def name(self) -> str:
                return "my_cell"

            @property
            def prefix(self) -> str:
                return "/api/my-cell"

            def get_router(self) -> APIRouter:
                from itl_braincell_sdk.cells.my_cell.routes import router
                return router

        cell = MyCell()
    """

    # ------------------------------------------------------------------
    # Required contract
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique cell identifier (snake_case, e.g. 'notes')."""
        ...

    @property
    @abstractmethod
    def prefix(self) -> str:
        """API route prefix, e.g. '/api/notes'."""
        ...

    @abstractmethod
    def get_router(self) -> APIRouter:
        """Return the FastAPI router for this cell's endpoints."""
        ...

    # ------------------------------------------------------------------
    # Optional: MCP integration
    # ------------------------------------------------------------------

    def register_mcp_tools(self, mcp: Any) -> None:
        """Register MCP tools for this cell.

        Override in subclasses to expose cell data via the Model Context
        Protocol.  Called automatically by the MCP server at startup via
        ``discover_cells()``.  The default implementation is a no-op so
        cells without MCP exposure are silently skipped.
        """

    # ------------------------------------------------------------------
    # Optional hooks (override as needed)
    # ------------------------------------------------------------------

    @property
    def tags(self) -> list[str]:
        """OpenAPI tags. Defaults to [name]."""
        return [self.name]

    def get_models(self) -> list:
        """Return SQLAlchemy model classes defined by this cell.

        Returning models here ensures they are imported before ``init_db()``
        runs, so their tables are created automatically via Base.metadata.
        """
        return []

    def on_startup(self, db: Session, weaviate_service: Any) -> dict:
        """Called during application startup after DB and Weaviate are ready.

        Use this to seed data, perform initial vector sync, or any other
        cell-specific startup work.

        Returns a stats dict (logged by the framework), e.g.
        ``{"synced": 5, "failed": 0}``.
        """
        return {}
