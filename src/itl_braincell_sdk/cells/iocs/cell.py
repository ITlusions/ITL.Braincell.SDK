"""IOC memory cell — auto-ingests and tracks indicators of compromise."""
import re
from fastapi import APIRouter

from itl_braincell_sdk.cells.base import MemoryCell

# Regex patterns for IOC auto-detection
_IOC_PATTERNS: dict[str, re.Pattern] = {
    "ip": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    "hash_sha256": re.compile(r'\b[a-f0-9]{64}\b', re.IGNORECASE),
    "hash_sha1": re.compile(r'\b[a-f0-9]{40}\b', re.IGNORECASE),
    "hash_md5": re.compile(r'\b[a-f0-9]{32}\b', re.IGNORECASE),
    "cve": re.compile(r'\bCVE-\d{4}-\d{4,}\b', re.IGNORECASE),
    "domain": re.compile(
        r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)'
        r'+(?:com|net|org|gov|mil|edu|io|ru|cn|de|nl|uk|fr|be|onion)\b',
        re.IGNORECASE,
    ),
}


def detect_iocs_in_text(text: str) -> list[tuple[str, str]]:
    """Return list of (ioc_type, value) tuples found in text."""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for ioc_type, pattern in _IOC_PATTERNS.items():
        for match in pattern.findall(text):
            value = match.lower() if ioc_type != "ip" else match
            if value not in seen:
                seen.add(value)
                found.append((ioc_type, value))
    return found


class IOCsCell(MemoryCell):
    """Memory cell for Indicators of Compromise — IPs, domains, hashes, CVEs with auto-detection."""

    @property
    def name(self) -> str:
        return "iocs"

    @property
    def prefix(self) -> str:
        return "/api/iocs"

    def get_router(self) -> APIRouter:
        from itl_braincell_sdk.cells.iocs.routes import router
        return router

    def get_models(self) -> list:
        from itl_braincell_sdk.cells.iocs.model import IOC
        return [IOC]

    def register_mcp_tools(self, mcp) -> None:
        from itl_braincell_sdk.core.database import SyncSessionLocal
        from itl_braincell_sdk.cells.iocs.model import IOC

        @mcp.tool()
        async def ioc_search(query: str, ioc_type: str | None = None, limit: int = 20) -> dict:
            """Search indicators of compromise — IPs, domains, hashes, CVEs.

            Use when asked 'is this IP malicious?', 'have we seen this hash?',
            'what IOCs are linked to this incident?', or 'is this CVE in our database?'.
            Optionally filter by ioc_type: ip / domain / hash_md5 / hash_sha1 / hash_sha256 / cve / url / email
            """
            db = SyncSessionLocal()
            try:
                wv_hits = []
                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_iocs(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "type": h.get("type"), "value": h.get("value")}
                        for h in wv_hits if h.get("archived")
                    ]
                    q = db.query(IOC).filter(IOC.id.in_([_UUID(i) for i in live_ids if i]))
                    if ioc_type:
                        q = q.filter(IOC.type == ioc_type)
                    rows = q.limit(limit).all()
                    return {
                        "query": query, "count": len(rows) + len(archived),
                        "results": [
                            {"id": str(r.id), "type": r.type, "value": r.value,
                             "confidence": r.confidence, "severity": r.severity,
                             "status": r.status, "source": r.source, "tags": r.tags}
                            for r in rows
                        ],
                        "archived": archived,
                    }
                # Exact + partial match fallback
                q = db.query(IOC).filter(IOC.status == "active")
                if ioc_type:
                    q = q.filter(IOC.type == ioc_type)
                exact = q.filter(IOC.value == query).limit(limit).all()
                partial = q.filter(IOC.value.ilike(f"%{query.lower()}%")).limit(limit).all()
                rows = exact or partial
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "type": r.type, "value": r.value,
                     "confidence": r.confidence, "severity": r.severity,
                     "source": r.source, "tags": r.tags}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def ioc_save(
            ioc_type: str,
            value: str,
            severity: str = "medium",
            confidence: float = 0.5,
            source: str | None = None,
            context: str | None = None,
            tags: list[str] | None = None,
            incident_refs: list[str] | None = None,
            threat_actor_refs: list[str] | None = None,
            tlp_level: str = "GREEN",
        ) -> dict:
            """Save an indicator of compromise to BrainCell memory.

            Automatically deduplicates by type + value.
            ioc_type: ip / domain / hash_md5 / hash_sha1 / hash_sha256 / url / email / cve / yara
            severity: critical / high / medium / low
            tlp_level: WHITE / GREEN / AMBER / RED
            """
            from datetime import datetime, timezone
            db = SyncSessionLocal()
            try:
                from itl_braincell_sdk.cells.iocs.model import IOC as _IOC
                existing = db.query(_IOC).filter(_IOC.type == ioc_type, _IOC.value == value).first()
                if existing:
                    existing.last_seen = datetime.now(timezone.utc)
                    if confidence > (existing.confidence or 0):
                        existing.confidence = confidence
                    db.commit()
                    return {"status": "updated", "id": str(existing.id), "type": ioc_type, "value": value}

                now = datetime.now(timezone.utc)
                ioc = _IOC(
                    type=ioc_type,
                    value=value,
                    severity=severity,
                    confidence=confidence,
                    source=source,
                    context=context,
                    tags=tags or [],
                    incident_refs=incident_refs or [],
                    threat_actor_refs=threat_actor_refs or [],
                    tlp_level=tlp_level,
                    status="active",
                    first_seen=now,
                    last_seen=now,
                )
                db.add(ioc)
                db.commit()
                db.refresh(ioc)

                try:
                    from itl_braincell_sdk.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_ioc(str(ioc.id), ioc_type, value, context)
                except Exception:
                    pass

                return {"status": "saved", "id": str(ioc.id), "type": ioc_type, "value": value}
            finally:
                db.close()

        @mcp.tool()
        async def ioc_scan_text(text: str, auto_save: bool = True, source: str = "auto-detect") -> dict:
            """Scan freeform text for indicators of compromise and optionally save them.

            Use when pasting log output, threat reports, or any text that may
            contain IPs, domains, hashes, or CVEs.
            Returns all detected IOCs and saves them if auto_save=True.
            """
            detected = detect_iocs_in_text(text)
            if not detected:
                return {"detected": 0, "iocs": []}

            saved = []
            if auto_save:
                from datetime import datetime, timezone
                db = SyncSessionLocal()
                try:
                    from itl_braincell_sdk.cells.iocs.model import IOC as _IOC
                    now = datetime.now(timezone.utc)
                    for ioc_type, value in detected:
                        existing = db.query(_IOC).filter(_IOC.type == ioc_type, _IOC.value == value).first()
                        if existing:
                            existing.last_seen = now
                            db.commit()
                            saved.append({"type": ioc_type, "value": value, "status": "updated"})
                        else:
                            ioc = _IOC(
                                type=ioc_type, value=value,
                                source=source, status="active",
                                first_seen=now, last_seen=now,
                                confidence=0.3,
                            )
                            db.add(ioc)
                            db.commit()
                            db.refresh(ioc)
                            saved.append({"type": ioc_type, "value": value, "id": str(ioc.id), "status": "new"})
                finally:
                    db.close()

            return {"detected": len(detected), "iocs": saved or [{"type": t, "value": v} for t, v in detected]}


cell = IOCsCell()
