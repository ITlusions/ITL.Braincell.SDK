"""Tasks memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class TasksCell(MemoryCell):
    """Memory cell for tasks and backlog items — create, track, and close work items."""

    @property
    def name(self) -> str:
        return "tasks"

    @property
    def prefix(self) -> str:
        return "/api/tasks"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.tasks.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.tasks.model import Task
        return [Task]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.tasks.model import Task

        @mcp.tool()
        async def tasks_search(query: str, limit: int = 20) -> dict:
            """Search tasks and backlog items by title, project, or description.

            Use to find existing tasks before creating duplicates, or to check
            the status of known work. Filters by open/in_progress by default.
            For a full overview use tasks_list.
            """
            db = SyncSessionLocal()
            try:
                q = query.lower()
                rows = db.query(Task).filter(
                    Task.title.ilike(f"%{q}%") |
                    Task.description.ilike(f"%{q}%") |
                    Task.project.ilike(f"%{q}%") |
                    Task.assignee.ilike(f"%{q}%")
                ).order_by(Task.created_at.desc()).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "title": r.title, "status": r.status,
                     "priority": r.priority, "project": r.project, "assignee": r.assignee}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def tasks_save(
            title: str,
            description: str | None = None,
            status: str = "open",
            priority: str = "medium",
            assignee: str | None = None,
            project: str | None = None,
            tags: list[str] | None = None,
        ) -> dict:
            """Create or update a task in the backlog.

            Use when a new action item, ticket, or follow-up needs to be tracked.
            status values: open / in_progress / done / cancelled / blocked
            priority values: critical / high / medium / low
            Always set project when known. Use assignee for ownership.
            """
            if not title:
                return {"error": "title is required"}
            db = SyncSessionLocal()
            try:
                row = Task(
                    title=title,
                    description=description,
                    status=status,
                    priority=priority,
                    assignee=assignee,
                    project=project,
                    tags=tags or [],
                    retention_days=90 if status == "done" else 0,
                    retain_reason="open task — permanent" if status != "done" else "completed task",
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return {"success": True, "id": str(row.id), "title": title,
                        "status": status, "priority": priority, "project": project}
            finally:
                db.close()

        @mcp.tool()
        async def tasks_list(
            status_filter: str | None = None,
            project: str | None = None,
            limit: int = 50,
        ) -> dict:
            """List tasks, optionally filtered by status and/or project.

            Use for a sprint overview, project backlog view, or 'what's open' queries.
            Leave status_filter empty to get all tasks. Use 'open' to see pending work.
            """
            db = SyncSessionLocal()
            try:
                query = db.query(Task)
                if status_filter:
                    query = query.filter(Task.status == status_filter)
                if project:
                    query = query.filter(Task.project == project)
                rows = query.order_by(Task.priority.desc(), Task.created_at.desc()).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "title": r.title, "status": r.status,
                     "priority": r.priority, "project": r.project,
                     "assignee": r.assignee, "tags": r.tags or []}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def tasks_close(task_id: str, resolution: str | None = None) -> dict:
            """Mark a task as done.

            Use when the user confirms a task or action item is completed.
            Optionally record the resolution summary.
            """
            from uuid import UUID as _UUID
            from datetime import datetime, timezone
            db = SyncSessionLocal()
            try:
                task = db.query(Task).filter(Task.id == _UUID(task_id)).first()
                if not task:
                    return {"error": "Task not found", "id": task_id}
                task.status = "done"
                task.completed_at = datetime.now(timezone.utc)
                task.retention_days = 90
                task.retain_reason = "completed task"
                if resolution:
                    task.description = (task.description or "") + f"\n\nResolution: {resolution}"
                db.commit()
                return {"success": True, "id": task_id, "title": task.title}
            finally:
                db.close()


cell = TasksCell()
