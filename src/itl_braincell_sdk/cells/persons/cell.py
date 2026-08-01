"""Persons memory cell — people and their roles."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class PersonsCell(MemoryCell):
    """Memory cell for people, their roles, teams, and responsibilities."""

    @property
    def name(self) -> str:
        return "persons"

    @property
    def prefix(self) -> str:
        return "/api/persons"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.persons.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.persons.model import Person
        return [Person]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.persons.model import Person

        @mcp.tool()
        async def person_save(
            name: str,
            role: str | None = None,
            responsibilities: list[str] | None = None,
            contact_info: str | None = None,
            team: str | None = None,
            tags: list[str] | None = None,
        ) -> dict:
            """Save a person with their role and team to memory.

            Use when a person is introduced or their role/responsibilities
            are described. Helps maintain context about stakeholders, owners,
            and collaborators across sessions.
            """
            if not name:
                return {"error": "name is required"}
            db = SyncSessionLocal()
            try:
                row = Person(
                    name=name,
                    role=role,
                    responsibilities=responsibilities or [],
                    contact_info=contact_info,
                    team=team,
                    tags=tags or [],
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return {"success": True, "id": str(row.id), "name": name, "role": role}
            finally:
                db.close()

        @mcp.tool()
        async def person_search(query: str, limit: int = 10) -> dict:
            """Search persons by name, role, team, or responsibilities.

            Use to recall who owns something, who to contact, or which team
            is responsible for a component or area.
            """
            db = SyncSessionLocal()
            try:
                q = query.lower()
                rows = db.query(Person).filter(
                    Person.name.ilike(f"%{q}%") |
                    Person.role.ilike(f"%{q}%") |
                    Person.team.ilike(f"%{q}%") |
                    Person.contact_info.ilike(f"%{q}%")
                ).order_by(Person.name).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "name": r.name, "role": r.role,
                     "team": r.team, "contact_info": r.contact_info,
                     "responsibilities": r.responsibilities or []}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def person_list(team: str | None = None, limit: int = 50) -> dict:
            """List all known persons, optionally filtered by team.

            Use for an overview of all recorded people or to see everyone
            on a specific team.
            """
            db = SyncSessionLocal()
            try:
                query = db.query(Person)
                if team:
                    query = query.filter(Person.team == team)
                rows = query.order_by(Person.name).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "name": r.name, "role": r.role,
                     "team": r.team, "tags": r.tags or []}
                    for r in rows
                ]}
            finally:
                db.close()


cell = PersonsCell()
