"""Runbooks memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class RunbooksCell(MemoryCell):
    """Memory cell for operational runbooks — step-by-step procedures for incidents, deployments, maintenance."""

    @property
    def name(self) -> str:
        return "runbooks"

    @property
    def prefix(self) -> str:
        return "/api/runbooks"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.runbooks.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.runbooks.model import Runbook
        return [Runbook]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.runbooks.model import Runbook

        @mcp.tool()
        async def runbooks_search(query: str, category: str | None = None, limit: int = 10) -> dict:
            """Search operational runbooks by title, trigger, category, or affected service.

            Use when an incident occurs, a deployment is planned, or a maintenance task needs a procedure.
            category values: incident_response / deployment / maintenance / onboarding / backup / rollback
            Not for code patterns — use snippets_search. Not for architecture decisions — use decisions_search.
            """
            db = SyncSessionLocal()
            try:
                q = query.lower()
                query_obj = db.query(Runbook).filter(
                    Runbook.title.ilike(f"%{q}%") |
                    Runbook.description.ilike(f"%{q}%") |
                    Runbook.trigger.ilike(f"%{q}%") |
                    Runbook.prerequisites.ilike(f"%{q}%")
                )
                if category:
                    query_obj = query_obj.filter(Runbook.category == category)
                rows = query_obj.order_by(Runbook.last_used_at.desc().nullslast()).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "title": r.title, "category": r.category,
                     "trigger": r.trigger, "severity": r.severity,
                     "services": r.services or [], "step_count": len(r.steps or [])}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def runbooks_save(
            title: str,
            steps: list[dict],
            description: str | None = None,
            category: str | None = None,
            trigger: str | None = None,
            prerequisites: str | None = None,
            rollback_steps: list[dict] | None = None,
            severity: str | None = None,
            services: list[str] | None = None,
            tags: list[str] | None = None,
        ) -> dict:
            """Save an operational runbook to memory.

            Use when a repeatable operational procedure is described.
            steps format: [{"step": 1, "title": "...", "command": "...", "expected_output": "...", "notes": "..."}]
            category values: incident_response / deployment / maintenance / onboarding / backup / rollback
            Always include rollback_steps when applicable.
            """
            if not title or not steps:
                return {"error": "title and steps are required"}
            db = SyncSessionLocal()
            try:
                row = Runbook(
                    title=title,
                    description=description,
                    category=category,
                    trigger=trigger,
                    prerequisites=prerequisites,
                    steps=steps,
                    rollback_steps=rollback_steps or [],
                    severity=severity,
                    services=services or [],
                    tags=tags or [],
                    retention_days=0,
                    retain_reason="operational knowledge — permanent",
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return {"success": True, "id": str(row.id), "title": title,
                        "category": category, "step_count": len(steps)}
            finally:
                db.close()

        @mcp.tool()
        async def runbooks_get(runbook_id: str) -> dict:
            """Retrieve the full steps of a runbook by ID.

            Use when a runbook was found via runbooks_search and the user wants
            to execute or review the complete procedure.
            """
            from uuid import UUID as _UUID
            db = SyncSessionLocal()
            try:
                row = db.query(Runbook).filter(Runbook.id == _UUID(runbook_id)).first()
                if not row:
                    return {"error": "Runbook not found", "id": runbook_id}
                return {
                    "id": str(row.id),
                    "title": row.title,
                    "description": row.description,
                    "category": row.category,
                    "trigger": row.trigger,
                    "prerequisites": row.prerequisites,
                    "steps": row.steps or [],
                    "rollback_steps": row.rollback_steps or [],
                    "severity": row.severity,
                    "services": row.services or [],
                    "last_used_at": str(row.last_used_at) if row.last_used_at else None,
                    "tags": row.tags or [],
                }
            finally:
                db.close()


cell = RunbooksCell()
