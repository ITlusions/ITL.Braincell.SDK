"""Kill chains memory cell — campaign-level attack lifecycle tracking across Lockheed / MITRE phases."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class KillChainsCell(MemoryCell):
    """Memory cell for kill chain campaigns — tracks multi-phase attack progression
    with per-phase techniques, tools, IOC references, and MITRE ATT&CK mappings."""

    @property
    def name(self) -> str:
        return "kill_chains"

    @property
    def prefix(self) -> str:
        return "/api/kill-chains"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.kill_chains.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.kill_chains.model import KillChain
        return [KillChain]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.kill_chains.model import KillChain

        @mcp.tool()
        async def kill_chain_search(query: str, limit: int = 10) -> dict:
            """Search kill chain campaigns by name, description, threat actor, or objective.

            Use when asked 'show me all active campaigns', 'what attack chain does APT29 use?',
            'which campaigns reached the C2 phase?', or 'find espionage kill chains'.
            Returns campaign records with phases, MITRE techniques, and IOC references.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_kill_chains(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if h.get("embedding_id")]
                    rows = db.query(KillChain).filter(
                        KillChain.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {
                        "query": query,
                        "count": len(rows),
                        "results": [_chain_summary(r) for r in rows],
                    }
                q = query.lower()
                rows = (
                    db.query(KillChain)
                    .filter(
                        KillChain.name.ilike(f"%{q}%")
                        | KillChain.description.ilike(f"%{q}%")
                        | KillChain.threat_actor_ref.ilike(f"%{q}%")
                        | KillChain.objective.ilike(f"%{q}%")
                    )
                    .limit(limit)
                    .all()
                )
                return {"query": query, "count": len(rows), "results": [_chain_summary(r) for r in rows]}
            finally:
                db.close()

        @mcp.tool()
        async def kill_chain_save(
            name: str,
            framework: str = "lockheed",
            status: str = "active",
            threat_actor_ref: str | None = None,
            target_org: str | None = None,
            objective: str | None = None,
            description: str | None = None,
            phases: list[dict] | None = None,
            mitre_techniques: list[str] | None = None,
            ioc_refs: list[str] | None = None,
            incident_refs: list[str] | None = None,
            classification_level: str = "UNCLASSIFIED",
            tlp_level: str = "AMBER",
            attribution_confidence: float | None = None,
            tags: list[str] | None = None,
        ) -> dict:
            """Save a new kill chain campaign record.

            Use when asked to 'log this campaign', 'track this attack sequence',
            or 'create a kill chain for this threat actor'.
            Provide phases as a list of dicts with keys: phase, order, status,
            techniques, tools_used, ioc_refs, snippet_refs, timestamp, notes.
            """
            db = SyncSessionLocal()
            try:
                row = KillChain(
                    name=name,
                    framework=framework,
                    status=status,
                    threat_actor_ref=threat_actor_ref,
                    target_org=target_org,
                    objective=objective,
                    description=description,
                    phases=phases or [],
                    mitre_techniques=mitre_techniques or [],
                    ioc_refs=ioc_refs or [],
                    incident_refs=incident_refs or [],
                    classification_level=classification_level,
                    tlp_level=tlp_level,
                    attribution_confidence=attribution_confidence,
                    tags=tags or [],
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_kill_chain(
                        str(row.id), row.name, row.description,
                        row.threat_actor_ref, row.objective,
                    )
                except Exception:
                    pass
                return {"saved": True, "id": str(row.id), "name": row.name}
            finally:
                db.close()

        @mcp.tool()
        async def kill_chain_advance_phase(
            chain_id: str,
            phase: str,
            status: str = "completed",
            techniques: list[str] | None = None,
            tools_used: list[str] | None = None,
            ioc_refs: list[str] | None = None,
            notes: str | None = None,
        ) -> dict:
            """Mark a kill chain phase as reached / completed.

            Use when asked to 'advance this campaign to C2 phase', 'mark exploitation complete',
            or 'update kill chain with new IOCs discovered in lateral movement'.
            Upserts the phase entry — safe to call multiple times.
            """
            from uuid import UUID as _UUID
            db = SyncSessionLocal()
            try:
                row = db.query(KillChain).filter(KillChain.id == _UUID(chain_id)).first()
                if not row:
                    return {"error": f"Kill chain {chain_id} not found"}
                phases = list(row.phases or [])
                update = {
                    "phase": phase,
                    "status": status,
                    **({"techniques": techniques} if techniques else {}),
                    **({"tools_used": tools_used} if tools_used else {}),
                    **({"ioc_refs": ioc_refs} if ioc_refs else {}),
                    **({"notes": notes} if notes else {}),
                }
                for existing in phases:
                    if existing.get("phase") == phase:
                        existing.update(update)
                        break
                else:
                    phases.append(update)
                row.phases = phases
                db.commit()
                return {"updated": True, "chain_id": chain_id, "phase": phase, "status": status}
            finally:
                db.close()


def _chain_summary(r) -> dict:
    return {
        "id": str(r.id),
        "name": r.name,
        "framework": r.framework,
        "status": r.status,
        "threat_actor_ref": r.threat_actor_ref,
        "target_org": r.target_org,
        "objective": r.objective,
        "phase_count": len(r.phases or []),
        "phases_completed": sum(
            1 for p in (r.phases or []) if p.get("status") == "completed"
        ),
        "mitre_techniques": r.mitre_techniques,
        "ioc_refs": r.ioc_refs,
        "tlp_level": r.tlp_level,
        "classification_level": r.classification_level,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


cell = KillChainsCell()
