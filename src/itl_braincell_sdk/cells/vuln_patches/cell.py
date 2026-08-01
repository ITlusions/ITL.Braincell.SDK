"""VulnPatch memory cell — known-vulnerable code + patched counterparts."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class VulnPatchesCell(MemoryCell):
    """Memory cell that stores known-vulnerable code snippets alongside their patched versions.

    Each record contains:
    - The original vulnerable code
    - The fixed/patched version
    - Explanation of what changed and why
    - CVE / CWE / OWASP references
    - Language, category, severity

    MCP tools: vuln_patches_search · vuln_patches_save · vuln_patches_lookup_cve
    """

    @property
    def name(self) -> str:
        return "vuln_patches"

    @property
    def prefix(self) -> str:
        return "/api/vuln_patches"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.vuln_patches.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.vuln_patches.model import VulnPatch
        return [VulnPatch]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.vuln_patches.model import VulnPatch

        @mcp.tool()
        async def vuln_patches_search(query: str, language: str | None = None, limit: int = 10) -> dict:
            """Search the database of known-vulnerable / patched code pairs.

            Use when asked:
            - 'Is this code pattern vulnerable?'
            - 'How should this be fixed?'
            - 'What is the secure equivalent of this snippet?'
            - 'Do we have a patch for CVE-XXXX-XXXX?'

            Returns vulnerable_code, patched_code, patch_explanation, CVE/CWE refs and severity.
            Optionally filter by language (python, javascript, java, c, go, ...).
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_vuln_patches(query, limit=limit * 2)
                except Exception:
                    pass

                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [
                        h["embedding_id"] for h in wv_hits
                        if not h.get("archived") and h.get("embedding_id")
                    ]
                    q = db.query(VulnPatch).filter(VulnPatch.id.in_(
                        [_UUID(i) for i in live_ids]
                    ))
                    if language:
                        q = q.filter(VulnPatch.language == language)
                    rows = q.limit(limit).all()
                else:
                    from sqlalchemy import or_
                    q = db.query(VulnPatch).filter(
                        or_(
                            VulnPatch.title.ilike(f"%{query}%"),
                            VulnPatch.description.ilike(f"%{query}%"),
                            VulnPatch.vulnerable_code.ilike(f"%{query}%"),
                            VulnPatch.patched_code.ilike(f"%{query}%"),
                            VulnPatch.patch_explanation.ilike(f"%{query}%"),
                            VulnPatch.category.ilike(f"%{query}%"),
                        )
                    )
                    if language:
                        q = q.filter(VulnPatch.language == language)
                    rows = q.limit(limit).all()

                return {
                    "results": [
                        {
                            "id": str(r.id),
                            "title": r.title,
                            "language": r.language,
                            "category": r.category,
                            "severity": r.severity,
                            "vulnerable_code": r.vulnerable_code,
                            "patched_code": r.patched_code,
                            "patch_explanation": r.patch_explanation,
                            "cve_refs": r.cve_refs or [],
                            "cwe_refs": r.cwe_refs or [],
                            "owasp_refs": r.owasp_refs or [],
                        }
                        for r in rows
                    ],
                    "count": len(rows),
                }
            finally:
                db.close()

        @mcp.tool()
        async def vuln_patches_save(
            title: str,
            vulnerable_code: str,
            patched_code: str,
            severity: str = "high",
            language: str | None = None,
            category: str | None = None,
            description: str | None = None,
            patch_explanation: str | None = None,
            cve_refs: list[str] | None = None,
            cwe_refs: list[str] | None = None,
            owasp_refs: list[str] | None = None,
            source: str | None = None,
            tags: list[str] | None = None,
            retention_days: int = 0,
        ) -> dict:
            """Save a known-vulnerable code snippet together with its patched equivalent.

            Use when:
            - A CVE with a code example is discussed
            - A security fix is implemented that others should know about
            - A code review reveals a vulnerability and the correct pattern

            severity: critical / high / medium / low
            category: sql_injection / xss / buffer_overflow / path_traversal / ssrf / idor / deserialization / ...
            cve_refs: list of CVE IDs, e.g. ['CVE-2021-44228']
            cwe_refs: list of CWE IDs, e.g. ['CWE-89']
            owasp_refs: list of OWASP categories, e.g. ['A03:2021']
            retention_days: 0 = keep forever (default for security knowledge)
            """
            db = SyncSessionLocal()
            try:
                from itl_braincell_sdk.services.retention_policy import evaluate as _retention
                retention = _retention("vuln_patches", {
                    "title": title,
                    "vulnerable_code": vulnerable_code,
                    "patched_code": patched_code,
                    "severity": severity,
                })
                if not retention.should_save:
                    return {"saved": False, "reason": retention.reason}

                entry = VulnPatch(
                    title=title,
                    vulnerable_code=vulnerable_code,
                    patched_code=patched_code,
                    severity=severity,
                    language=language,
                    category=category,
                    description=description,
                    patch_explanation=patch_explanation,
                    cve_refs=cve_refs or [],
                    cwe_refs=cwe_refs or [],
                    owasp_refs=owasp_refs or [],
                    source=source or "manual",
                    tags=tags or [],
                    retention_days=retention_days if retention_days else retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=None if retention_days == 0 else retention.expires_at,
                )
                db.add(entry)
                db.commit()
                db.refresh(entry)

                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_vuln_patch(
                        str(entry.id),
                        title=title,
                        description=description or "",
                        vulnerable_code=vulnerable_code,
                        patched_code=patched_code,
                        patch_explanation=patch_explanation or "",
                    )
                except Exception:
                    pass

                return {
                    "saved": True,
                    "id": str(entry.id),
                    "severity": entry.severity,
                    "cve_refs": entry.cve_refs,
                    "retention_days": entry.retention_days,
                }
            finally:
                db.close()

        @mcp.tool()
        async def vuln_patches_lookup_cve(cve_id: str) -> dict:
            """Look up all known-vulnerable / patched code entries that reference a specific CVE.

            Use when asked 'do we have a patch for CVE-2021-44228?' or
            'show me all vulnerable patterns related to Log4Shell'.
            """
            db = SyncSessionLocal()
            try:
                from sqlalchemy import cast
                from sqlalchemy.dialects.postgresql import JSONB
                rows = (
                    db.query(VulnPatch)
                    .filter(cast(VulnPatch.cve_refs, JSONB).contains([cve_id]))
                    .all()
                )
                return {
                    "cve_id": cve_id,
                    "count": len(rows),
                    "entries": [
                        {
                            "id": str(r.id),
                            "title": r.title,
                            "language": r.language,
                            "severity": r.severity,
                            "category": r.category,
                            "vulnerable_code": r.vulnerable_code,
                            "patched_code": r.patched_code,
                            "patch_explanation": r.patch_explanation,
                            "cwe_refs": r.cwe_refs or [],
                            "owasp_refs": r.owasp_refs or [],
                        }
                        for r in rows
                    ],
                }
            finally:
                db.close()


cell = VulnPatchesCell()
