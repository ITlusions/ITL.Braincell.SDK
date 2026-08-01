"""Api contracts memory cell."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class ApiContractsCell(MemoryCell):
    """Memory cell for API contracts — specifications, versions, endpoints, and changelogs."""

    @property
    def name(self) -> str:
        return "api_contracts"

    @property
    def prefix(self) -> str:
        return "/api/api_contracts"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.api_contracts.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.api_contracts.model import ApiContract
        return [ApiContract]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.api_contracts.model import ApiContract

        @mcp.tool()
        async def api_contracts_search(query: str, limit: int = 10) -> dict:
            """Search stored API contracts by service name, version, or endpoint path.

            Use when integrating with or generating code against a known API.
            Returns contract summaries including base_url, spec_format, status, and endpoint count.
            For architecture decisions around API design use decisions_search.
            For known vulnerable dependencies use dependencies_search.
            """
            db = SyncSessionLocal()
            try:
                q = query.lower()
                rows = db.query(ApiContract).filter(
                    ApiContract.title.ilike(f"%{q}%") |
                    ApiContract.service_name.ilike(f"%{q}%") |
                    ApiContract.version.ilike(f"%{q}%") |
                    ApiContract.spec_content.ilike(f"%{q}%")
                ).order_by(ApiContract.created_at.desc()).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "title": r.title, "service_name": r.service_name,
                     "version": r.version, "base_url": r.base_url,
                     "spec_format": r.spec_format, "status": r.status,
                     "endpoint_count": len(r.endpoints or [])}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def api_contracts_save(
            title: str,
            service_name: str,
            version: str,
            spec_format: str | None = None,
            base_url: str | None = None,
            spec_content: str | None = None,
            status: str = "active",
            breaking_changes: str | None = None,
            endpoints: list[dict] | None = None,
            auth_type: str | None = None,
            tags: list[str] | None = None,
        ) -> dict:
            """Save an API contract specification to memory.

            Use when a new API version is released, an interface is discussed,
            or an OpenAPI/GraphQL/gRPC spec is referenced.
            spec_format values: openapi / graphql / grpc / rest / soap
            status values: active / deprecated / draft / sunset
            auth_type values: bearer / apikey / oauth2 / none
            Always set base_url and version. Store endpoints as [{method, path, summary}].
            """
            if not title or not service_name or not version:
                return {"error": "title, service_name, and version are required"}
            db = SyncSessionLocal()
            try:
                row = ApiContract(
                    title=title,
                    service_name=service_name,
                    version=version,
                    spec_format=spec_format,
                    base_url=base_url,
                    spec_content=spec_content,
                    status=status,
                    breaking_changes=breaking_changes,
                    endpoints=endpoints or [],
                    auth_type=auth_type,
                    tags=tags or [],
                    retention_days=0,
                    retain_reason="API contract — permanent",
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return {"success": True, "id": str(row.id), "service_name": service_name,
                        "version": version, "status": status}
            finally:
                db.close()

        @mcp.tool()
        async def api_contracts_list_services(limit: int = 50) -> dict:
            """List all services that have stored API contracts, with their latest version.

            Use for a quick overview of known APIs and their status.
            """
            db = SyncSessionLocal()
            try:
                rows = db.query(ApiContract).order_by(
                    ApiContract.service_name, ApiContract.version.desc()
                ).limit(limit).all()
                seen: dict[str, dict] = {}
                for r in rows:
                    if r.service_name not in seen:
                        seen[r.service_name] = {
                            "service_name": r.service_name,
                            "latest_version": r.version,
                            "status": r.status,
                            "spec_format": r.spec_format,
                            "base_url": r.base_url,
                        }
                return {"count": len(seen), "services": list(seen.values())}
            finally:
                db.close()


cell = ApiContractsCell()
