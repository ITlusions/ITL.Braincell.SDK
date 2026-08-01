"""Incidents memory cell — tracks security incidents, timelines, and response actions."""
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell


class IncidentsCell(MemoryCell):
    """Memory cell for security incidents — SIRP-style tracking with timeline and attribution."""

    @property
    def name(self) -> str:
        return "incidents"

    @property
    def prefix(self) -> str:
        return "/api/incidents"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.incidents.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.incidents.model import SecurityIncident
        return [SecurityIncident]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.incidents.model import SecurityIncident

        @mcp.tool()
        async def incidents_search(query: str, limit: int = 10) -> dict:
            """Search security incidents by title, description, attack vector, or threat actor name.

            Use when asked 'have we seen this attack before?', 'what incidents are open?',
            'which incidents involve phishing?', or 'show me critical incidents this month'.
            Returns incident records with severity, status, timeline, and IOC references.
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_incidents(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "title": h.get("title"), "severity": h.get("severity")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(SecurityIncident).filter(
                        SecurityIncident.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {
                        "query": query, "count": len(rows) + len(archived),
                        "results": [
                            {"id": str(r.id), "title": r.title, "severity": r.severity,
                             "status": r.status, "attack_vector": r.attack_vector,
                             "threat_actor_name": r.threat_actor_name,
                             "mitre_tactics": r.mitre_tactics,
                             "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                             "ioc_refs": r.ioc_refs}
                            for r in rows
                        ],
                        "archived": archived,
                    }
                q = query.lower()
                rows = db.query(SecurityIncident).filter(
                    SecurityIncident.title.ilike(f"%{q}%") |
                    SecurityIncident.description.ilike(f"%{q}%") |
                    SecurityIncident.attack_vector.ilike(f"%{q}%") |
                    SecurityIncident.threat_actor_name.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "title": r.title, "severity": r.severity,
                     "status": r.status, "attack_vector": r.attack_vector,
                     "threat_actor_name": r.threat_actor_name,
                     "detected_at": r.detected_at.isoformat() if r.detected_at else None}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def incidents_save(
            title: str,
            severity: str = "medium",
            description: str | None = None,
            attack_vector: str | None = None,
            affected_assets: list[str] | None = None,
            mitre_tactics: list[str] | None = None,
            threat_actor_name: str | None = None,
            ioc_refs: list[str] | None = None,
            classification_level: str = "UNCLASSIFIED",
            tlp_level: str = "GREEN",
            retention_days: int | None = None,
        ) -> dict:
            """Save a new security incident to BrainCell memory.

            Use when a new security event is detected or reported.
            severity: critical / high / medium / low / info
            classification_level: UNCLASSIFIED / SENSITIVE / CONFIDENTIAL / SECRET
            tlp_level: WHITE / GREEN / AMBER / RED (Traffic Light Protocol)
            mitre_tactics: list of MITRE tactic IDs e.g. ['TA0001', 'TA0002']
            ioc_refs: IOC values observed in this incident (IPs, domains, hashes)
            """
            from datetime import datetime, timezone
            db = SyncSessionLocal()
            try:
                from itl_braincell_sdk.cells.incidents.model import SecurityIncident as _SI
                incident = _SI(
                    title=title,
                    description=description,
                    severity=severity,
                    status="open",
                    attack_vector=attack_vector,
                    affected_assets=affected_assets or [],
                    mitre_tactics=mitre_tactics or [],
                    threat_actor_name=threat_actor_name,
                    ioc_refs=ioc_refs or [],
                    classification_level=classification_level,
                    tlp_level=tlp_level,
                    detected_at=datetime.now(timezone.utc),
                )
                if retention_days is not None:
                    incident.retention_days = retention_days
                db.add(incident)
                db.commit()
                db.refresh(incident)

                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_incident(str(incident.id), title, description, severity)
                except Exception:
                    pass

                return {"status": "saved", "id": str(incident.id), "title": incident.title, "severity": incident.severity}
            finally:
                db.close()

        @mcp.tool()
        async def incidents_add_timeline(
            incident_id: str,
            event: str,
            analyst: str | None = None,
        ) -> dict:
            """Add a timestamped event to an incident timeline.

            Use to record investigation steps, containment actions,
            or evidence findings during an active incident response.
            """
            from datetime import datetime, timezone
            from uuid import UUID as _UUID
            db = SyncSessionLocal()
            try:
                incident = db.query(SecurityIncident).filter(
                    SecurityIncident.id == _UUID(incident_id)
                ).first()
                if not incident:
                    return {"error": "Incident not found", "incident_id": incident_id}
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": event,
                    "analyst": analyst,
                }
                current = list(incident.timeline or [])
                current.append(entry)
                incident.timeline = current
                db.commit()
                return {"status": "added", "incident_id": incident_id, "timeline_length": len(current)}
            finally:
                db.close()


cell = IncidentsCell()
