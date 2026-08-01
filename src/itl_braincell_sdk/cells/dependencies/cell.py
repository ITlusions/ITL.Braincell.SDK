"""Dependencies memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class DependenciesCell(MemoryCell):
    """Memory cell for software dependencies — track packages, versions, licenses, and CVE exposure."""

    @property
    def name(self) -> str:
        return "dependencies"

    @property
    def prefix(self) -> str:
        return "/api/dependencies"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.dependencies.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.dependencies.model import Dependency
        return [Dependency]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.dependencies.model import Dependency

        @mcp.tool()
        async def dependencies_search(
            query: str,
            ecosystem: str | None = None,
            limit: int = 20,
        ) -> dict:
            """Search tracked software dependencies by name, project, or ecosystem.

            Use before adding a new library (check if already tracked), before code generation
            (check what versions are approved), or when a CVE is reported (find affected packages).
            ecosystem values: pypi / npm / nuget / maven / cargo / go / gem
            For CVE-specific lookup use dependencies_by_cve. For known exploits use vuln_patches_search.
            """
            db = SyncSessionLocal()
            try:
                q = query.lower()
                query_obj = db.query(Dependency).filter(
                    Dependency.name.ilike(f"%{q}%") |
                    Dependency.project.ilike(f"%{q}%") |
                    Dependency.notes.ilike(f"%{q}%")
                )
                if ecosystem:
                    query_obj = query_obj.filter(Dependency.ecosystem == ecosystem)
                rows = query_obj.order_by(Dependency.name).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "name": r.name, "version": r.version,
                     "ecosystem": r.ecosystem, "project": r.project,
                     "status": r.status, "license": r.license,
                     "cve_refs": r.cve_refs or [], "upgrade_to": r.upgrade_to}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def dependencies_save(
            name: str,
            version: str,
            ecosystem: str | None = None,
            project: str | None = None,
            license: str | None = None,
            status: str = "ok",
            cve_refs: list[str] | None = None,
            upgrade_to: str | None = None,
            notes: str | None = None,
            tags: list[str] | None = None,
        ) -> dict:
            """Track a software dependency in memory.

            Use when a library or package is discussed, added to a project, or found to be vulnerable.
            status values: ok / vulnerable / deprecated / outdated / unknown
            Set cve_refs and upgrade_to when status is 'vulnerable'.
            Always set ecosystem and project when known.
            """
            if not name or not version:
                return {"error": "name and version are required"}
            db = SyncSessionLocal()
            try:
                row = Dependency(
                    name=name,
                    version=version,
                    ecosystem=ecosystem,
                    project=project,
                    license=license,
                    status=status,
                    cve_refs=cve_refs or [],
                    upgrade_to=upgrade_to,
                    notes=notes,
                    tags=tags or [],
                    retention_days=0,
                    retain_reason="dependency tracking — permanent",
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return {"success": True, "id": str(row.id), "name": name,
                        "version": version, "ecosystem": ecosystem, "status": status}
            finally:
                db.close()

        @mcp.tool()
        async def dependencies_by_cve(cve_id: str) -> dict:
            """Find all tracked dependencies linked to a specific CVE.

            Use immediately when a CVE is mentioned to determine blast radius.
            Returns all packages across all projects that reference this CVE.
            For the patched code examples use vuln_patches_lookup_cve.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(Dependency).filter(
                    Dependency.cve_refs.contains([cve_id])
                ).all()
                return {"cve_id": cve_id, "affected_count": len(rows), "affected": [
                    {"id": str(r.id), "name": r.name, "version": r.version,
                     "ecosystem": r.ecosystem, "project": r.project,
                     "status": r.status, "upgrade_to": r.upgrade_to}
                    for r in rows
                ]}
            finally:
                db.close()


cell = DependenciesCell()
