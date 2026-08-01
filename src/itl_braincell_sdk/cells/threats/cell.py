"""Threats memory cell — tracks threat actors, TTPs, and attribution intelligence."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class ThreatsCell(MemoryCell):
    """Memory cell for threat actors — APTs, criminal groups, TTPs, MITRE ATT&CK mapping."""

    @property
    def name(self) -> str:
        return "threats"

    @property
    def prefix(self) -> str:
        return "/api/threats"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.threats.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.threats.model import ThreatActor
        return [ThreatActor]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.threats.model import ThreatActor

        @mcp.tool()
        async def threats_search(query: str, limit: int = 10) -> dict:
            """Search known threat actors by name, alias, classification, motivation, or TTP.

            Use when asked 'who is behind this attack?', 'which APT uses T1566?',
            'do we know this threat actor?', or 'which groups target our sector?'.
            Returns threat actor profiles with TTPs and attribution metadata.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_threat_actors(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "name": h.get("name"), "classification": h.get("classification")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(ThreatActor).filter(
                        ThreatActor.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {
                        "query": query, "count": len(rows) + len(archived),
                        "results": [
                            {"id": str(r.id), "name": r.name, "aliases": r.aliases,
                             "classification": r.classification, "motivation": r.motivation,
                             "sophistication": r.sophistication, "ttps": r.ttps,
                             "origin_country": r.origin_country, "status": r.status,
                             "confidence_score": r.confidence_score}
                            for r in rows
                        ],
                        "archived": archived,
                    }
                q = query.lower()
                rows = db.query(ThreatActor).filter(
                    ThreatActor.name.ilike(f"%{q}%") |
                    ThreatActor.classification.ilike(f"%{q}%") |
                    ThreatActor.motivation.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "name": r.name, "aliases": r.aliases,
                     "classification": r.classification, "motivation": r.motivation,
                     "sophistication": r.sophistication, "ttps": r.ttps,
                     "origin_country": r.origin_country, "status": r.status,
                     "confidence_score": r.confidence_score}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def threats_save(
            name: str,
            classification: str | None = None,
            origin_country: str | None = None,
            motivation: str | None = None,
            sophistication: str | None = None,
            ttps: list[str] | None = None,
            aliases: list[str] | None = None,
            confidence_score: float = 0.5,
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Save a threat actor profile to BrainCell memory.

            Use when identifying a new threat actor, attributing an attack,
            or adding MITRE ATT&CK TTPs to a known group.
            classification: apt / criminal / hacktivist / state-sponsored / unknown
            sophistication: low / medium / high / nation-state
            motivation: espionage / financial / disruption / ideological
            ttps: list of MITRE ATT&CK technique IDs e.g. ['T1566', 'T1059.001']
            """
            db = SyncSessionLocal()
            try:
                from itl_braincell_sdk.cells.threats.model import ThreatActor as _TA
                actor = _TA(
                    name=name,
                    classification=classification,
                    origin_country=origin_country,
                    motivation=motivation,
                    sophistication=sophistication,
                    ttps=ttps or [],
                    aliases=aliases or [],
                    confidence_score=confidence_score,
                    status="active",
                )
                if retention_days is not None:
                    actor.retention_days = retention_days
                if retain_reason:
                    actor.retain_reason = retain_reason
                db.add(actor)
                db.commit()
                db.refresh(actor)

                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_threat_actor(str(actor.id), name, classification, motivation, ttps or [])
                except Exception:
                    pass

                return {"status": "saved", "id": str(actor.id), "name": actor.name}
            finally:
                db.close()

        @mcp.tool()
        async def threats_ttp_lookup(ttp_id: str) -> dict:
            """Find all threat actors known to use a specific MITRE ATT&CK technique.

            Use when responding to an alert that matches a known TTP
            and you need to narrow down attribution.
            Example: threats_ttp_lookup('T1566') → returns all actors using phishing.
            """
            db = SyncSessionLocal()
            try:
                from sqlalchemy import cast, String as _Str
                rows = db.query(ThreatActor).filter(
                    cast(ThreatActor.ttps, _Str).ilike(f"%{ttp_id}%")
                ).all()
                return {
                    "ttp_id": ttp_id,
                    "count": len(rows),
                    "actors": [
                        {"id": str(r.id), "name": r.name, "classification": r.classification,
                         "origin_country": r.origin_country, "sophistication": r.sophistication}
                        for r in rows
                    ],
                }
            finally:
                db.close()


cell = ThreatsCell()
