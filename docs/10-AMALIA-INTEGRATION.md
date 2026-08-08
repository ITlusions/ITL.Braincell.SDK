# Amalia ↔ BrainCell Integration Guide

**Version**: 1.0.0  
**Status**: DRAFT (Sprint 3–5 Implementation Roadmap)  
**Last Updated**: 2026-08-04

---

## Table of Contents

1. [Overview](#overview)
2. [Current State: 3 Integration Gaps](#current-state-3-integration-gaps)
3. [Data Flow Architecture](#data-flow-architecture)
4. [3-Phase Integration Roadmap](#3-phase-integration-roadmap)
5. [Finding Storage Mapping](#finding-storage-mapping)
6. [Implementation Guide](#implementation-guide)
7. [Quick Wins](#quick-wins)
8. [Security Considerations](#security-considerations)
9. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## Overview

**Amalia** is an AI-powered threat detection platform with 20 collectors (OSINT, SIGINT, audio, GEOINT, FININT, dark web, vulnerability scanning) and 5 threat detectors (cyber, physical, communication, acoustic, vulnerability).

**BrainCell** is a persistent memory platform that stores domain-specific knowledge in plugin cells.

**Goal**: Make Amalia findings durably persistent in BrainCell memory, queryable by AI agents via MCP tools, and integrated into the multi-tenant intelligence workflow.

---

## Current State: 3 Integration Gaps

### Gap 1: No Ingest Pipeline
- **Problem**: Amalia findings (87/day) computed in-memory but lost when API restarts
- **Impact**: No institutional memory of threats discovered
- **Status**: Sprint 3 deliverable (not yet started)
- **Required for**: Findings persistence, historical analysis

### Gap 2: No MCP Tool Exposure
- **Problem**: Collectors not available to Claude/agents for autonomous queries
- **Impact**: Agents can't ask "what OSINT exists on this entity?" during analysis
- **Status**: Sprint 5 deliverable
- **Required for**: Autonomous agent workflows, real-time SIGINT integration

### Gap 3: No Real-Time Event Stream
- **Problem**: Synchronous API calls block Amalia if BrainCell is slow
- **Impact**: Threat detection latency increases; findings may be dropped
- **Status**: Sprint 4 deliverable (message queue)
- **Required for**: High-throughput ingestion, fault tolerance

---

## Data Flow Architecture

### Current (Broken) Flow

```
Amalia Detectors
    ↓
Findings (in-memory list)
    ↓
REST response → Lost on restart ❌
```

### Target State (3-Phase)

```
Phase 1 (Sprint 3):
    ↓
Amalia Detectors → REST /ingest/amalia-findings → BrainCell API
                                                        ↓
                                                    PostgreSQL
                                                    (persistent)

Phase 2 (Sprint 4):
    ↓
Amalia Detectors → Redis pub/sub → BrainCell async consumer
                                    (non-blocking)
                                        ↓
                                    PostgreSQL + Weaviate
                                    (semantic search)

Phase 3 (Sprint 5):
    ↓
BrainCell MCP Server ← MCP tool wrappers ← Amalia collectors
    ↓
Claude + Agents can query:
  - OSINT: "lookup domain example.com"
  - SIGINT: "monitor frequency 121.5 MHz"
  - VulnScan: "analyze binary /bin/curl"
```

---

## 3-Phase Integration Roadmap

### Phase 1: Synchronous API Integration ✅ (Sprint 3 — BLOCKING)

**What**: REST endpoint for Amalia findings ingestion  
**Effort**: 2–3 days (after Sprint 1 auth complete)  
**Status**: PLANNED (waiting for `/src/auth/permissions.py`)

#### Implementation

**Location**: `ITL.BrainCell.Api/src/api/routes/ingest.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class AmaliaThreatsPayload(BaseModel):
    """Amalia cyber/physical/communication/acoustic threat findings"""
    source: str = Field(default="amalia", description="Source system")
    detector_type: str = Field(..., description="cyber|physical|communication|acoustic")
    findings: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "source": "amalia",
                "detector_type": "cyber",
                "findings": [
                    {
                        "threat_id": "AMALIA-2026-08-001",
                        "threat_name": "Ransomware.LockBit",
                        "severity": "CRITICAL",
                        "confidence": 0.95,
                        "iocs": ["192.168.1.1", "example.com"],
                        "detected_at": "2026-08-04T12:30:00Z"
                    }
                ]
            }
        }

class AmaliaVulnerabilitiesPayload(BaseModel):
    """Amalia vulnerability scanner findings (SAST, binary analysis, ROP gadgets)"""
    detector_type: str = Field(default="vulnerability")
    findings: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "detector_type": "vulnerability",
                "findings": [
                    {
                        "vuln_id": "AMALIA-VULN-2026-08-001",
                        "cwe_id": "CWE-190",
                        "severity": "HIGH",
                        "cvss_score": 8.1,
                        "poc_available": True,
                        "file_path": "src/parser.c",
                        "line_range": [145, 152],
                        "vulnerability_type": "integer_overflow",
                        "exploit_chain": "6-phase privilege escalation",
                        "detected_at": "2026-08-04T12:30:00Z"
                    }
                ]
            }
        }

class AmaliaOSINTPayload(BaseModel):
    """Amalia OSINT findings (DNS, WHOIS, SSL, breach DB, etc.)"""
    detector_type: str = Field(default="osint")
    findings: List[dict]

class AmaliaIOCPayload(BaseModel):
    """Extracted IOCs from Amalia threat intelligence"""
    detector_type: str = Field(default="iocs")
    iocs: List[dict]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/amalia/threats")
async def ingest_amalia_threats(
    payload: AmaliaThreatsPayload,
    session: AsyncSession = Depends(get_session),
    tenant = Depends(require_tenant),
    user = Depends(require_role("itl-cell-writer"))
) -> dict:
    """
    Ingest Amalia threat findings (cyber, physical, communication, acoustic).
    
    Findings are stored in:
    - `threats` cell → primary threat records
    - `incidents` cell → if supply chain impact detected
    - `iocs` cell → extracted indicators
    """
    from itl_braincell_sdk.cells.threats.model import Threat
    from itl_braincell_sdk.cells.iocs.model import IOC
    
    stored_threats = []
    stored_iocs = []
    
    for finding in payload.findings:
        # Create threat record
        threat = Threat(
            tenant_id=tenant.id,
            threat_id=finding.get("threat_id"),
            threat_name=finding.get("threat_name"),
            detector="amalia:" + payload.detector_type,
            severity=finding.get("severity"),
            confidence=finding.get("confidence", 0.0),
            description=finding.get("description", ""),
            braincell_source="amalia",
            braincell_timestamp=datetime.utcnow()
        )
        session.add(threat)
        stored_threats.append(threat.id)
        
        # Extract IOCs from finding
        for ioc_str in finding.get("iocs", []):
            ioc = IOC(
                tenant_id=tenant.id,
                ioc_value=ioc_str,
                ioc_type=_classify_ioc(ioc_str),
                source_threat_id=threat.id,
                confidence=finding.get("confidence", 0.0),
                braincell_timestamp=datetime.utcnow()
            )
            session.add(ioc)
            stored_iocs.append(ioc.id)
    
    await session.commit()
    
    return {
        "status": "success",
        "ingested_threats": len(stored_threats),
        "ingested_iocs": len(stored_iocs),
        "threat_ids": stored_threats,
        "ioc_ids": stored_iocs,
        "detector_type": payload.detector_type
    }


@router.post("/amalia/vulnerabilities")
async def ingest_amalia_vulnerabilities(
    payload: AmaliaVulnerabilitiesPayload,
    session: AsyncSession = Depends(get_session),
    tenant = Depends(require_tenant),
    user = Depends(require_role("itl-cell-writer"))
) -> dict:
    """
    Ingest Amalia vulnerability scanner findings.
    
    Findings stored in:
    - `vuln_reports` cell → confirmed vulnerabilities + PoC
    - `code_inspection` cell → code location + context (once implemented)
    - `low_confidence_findings` cell → if confidence < 0.8 (for ensemble voting)
    """
    from itl_braincell_sdk.cells.vuln_reports.model import VulnReport
    
    stored = []
    
    for finding in payload.findings:
        vuln = VulnReport(
            tenant_id=tenant.id,
            vuln_id=finding.get("vuln_id"),
            cwe_id=finding.get("cwe_id"),
            severity=finding.get("severity"),
            cvss_score=finding.get("cvss_score", 0.0),
            poc_available=finding.get("poc_available", False),
            file_path=finding.get("file_path"),
            line_range=finding.get("line_range"),
            vulnerability_type=finding.get("vulnerability_type"),
            exploit_chain=finding.get("exploit_chain"),
            detector="amalia:vulnerability",
            braincell_source="amalia",
            braincell_timestamp=datetime.utcnow()
        )
        session.add(vuln)
        stored.append(vuln.id)
    
    await session.commit()
    
    return {
        "status": "success",
        "ingested_vulnerabilities": len(stored),
        "vuln_ids": stored
    }


@router.post("/amalia/osint")
async def ingest_amalia_osint(
    payload: AmaliaOSINTPayload,
    session: AsyncSession = Depends(get_session),
    tenant = Depends(require_tenant),
    user = Depends(require_role("itl-cell-writer"))
) -> dict:
    """
    Ingest Amalia OSINT findings (DNS, WHOIS, SSL certificates, breach DB).
    
    Note: Requires infrastructure_analysis cell implementation.
    For now, stored as raw findings in audit logs.
    """
    # TODO: Implement infrastructure_analysis cell in Sprint 4
    audit_log = {
        "event_type": "osint_ingest",
        "detector": "amalia:osint",
        "finding_count": len(payload.findings),
        "timestamp": datetime.utcnow().isoformat()
    }
    # Log to audit_logs cell (SDK)
    return {"status": "queued", "audit_log": audit_log}


@router.post("/amalia/iocs")
async def ingest_amalia_iocs(
    payload: AmaliaIOCPayload,
    session: AsyncSession = Depends(get_session),
    tenant = Depends(require_tenant),
    user = Depends(require_role("itl-cell-writer"))
) -> dict:
    """
    Ingest extracted IOCs from Amalia threat intelligence feeds.
    
    Findings stored in:
    - `iocs` cell → all extracted indicators
    """
    from itl_braincell_sdk.cells.iocs.model import IOC
    
    stored = []
    
    for ioc in payload.iocs:
        indicator = IOC(
            tenant_id=tenant.id,
            ioc_value=ioc.get("value"),
            ioc_type=ioc.get("type"),
            source=ioc.get("source", "amalia"),
            confidence=ioc.get("confidence", 0.0),
            braincell_timestamp=datetime.utcnow()
        )
        session.add(indicator)
        stored.append(indicator.id)
    
    await session.commit()
    
    return {
        "status": "success",
        "ingested_iocs": len(stored),
        "ioc_ids": stored
    }


# ============================================================================
# HELPERS
# ============================================================================

def _classify_ioc(value: str) -> str:
    """Classify IOC type: ip, domain, hash, url, email, etc."""
    if "://" in value:
        return "url"
    if "@" in value and "." in value:
        return "email"
    if len(value) in [32, 40, 64]:  # MD5, SHA1, SHA256
        return "hash"
    if "." in value and len(value) < 255:
        return "domain"
    if _is_ipv4(value):
        return "ip"
    return "unknown"

def _is_ipv4(value: str) -> bool:
    """Check if value is valid IPv4 address"""
    try:
        parts = value.split(".")
        return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)
    except:
        return False
```

#### Testing

```python
# test_amalia_ingest.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_ingest_amalia_threats(client: AsyncClient, auth_headers):
    """Test threat finding ingestion"""
    payload = {
        "detector_type": "cyber",
        "findings": [
            {
                "threat_id": "AMALIA-2026-08-001",
                "threat_name": "Ransomware.LockBit",
                "severity": "CRITICAL",
                "confidence": 0.95,
                "iocs": ["192.168.1.1", "example.com"],
                "detected_at": "2026-08-04T12:30:00Z"
            }
        ]
    }
    
    response = await client.post(
        "/api/ingest/amalia/threats",
        json=payload,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ingested_threats"] == 1
    assert len(data["ioc_ids"]) == 2
```

---

### Phase 2: Async Message Queue (Sprint 4)

**What**: Redis pub/sub for real-time, non-blocking findings ingestion  
**Effort**: 3–4 days  
**Benefit**: Amalia doesn't block; BrainCell consumes at own pace

#### Architecture

```
Amalia (async)
    ↓ (emit_finding)
Redis Channel: "amalia:findings:cyber"
    ↓
BrainCell Consumer (async task)
    ↓ (batch process 100 findings/sec)
PostgreSQL + Weaviate
    ↓
Query results + vector search
```

#### Implementation

**Location**: `ITL.BrainCell.Api/src/services/amalia_ingest_consumer.py`

```python
import asyncio
import json
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from pydantic import BaseModel
from typing import AsyncIterator

class AmaliaConsumer:
    """Real-time Amalia findings consumer"""
    
    def __init__(self, redis_url: str, db_session_factory):
        self.redis_url = redis_url
        self.session_factory = db_session_factory
        self.channels = [
            "amalia:findings:cyber",
            "amalia:findings:physical",
            "amalia:findings:vulnerability",
            "amalia:iocs:*"
        ]
        self.metrics = {
            "processed": 0,
            "errors": 0,
            "last_batch_size": 0
        }
    
    async def start(self):
        """Start consuming from Redis"""
        redis = await aioredis.from_url(self.redis_url)
        pubsub = redis.pubsub()
        
        await pubsub.psubscribe(*self.channels)
        
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                try:
                    finding = json.loads(message["data"])
                    await self._ingest_finding(finding)
                    self.metrics["processed"] += 1
                except Exception as e:
                    self.metrics["errors"] += 1
                    logger.error(f"Ingest error: {e}", extra={"finding": finding})
    
    async def _ingest_finding(self, finding: dict):
        """Ingest a single finding into BrainCell"""
        async with self.session_factory() as session:
            # Route by detector type
            if finding.get("detector_type") == "cyber":
                await self._ingest_threat(session, finding)
            elif finding.get("detector_type") == "vulnerability":
                await self._ingest_vulnerability(session, finding)
            elif finding.get("detector_type") == "iocs":
                await self._ingest_iocs(session, finding)
            
            await session.commit()
    
    async def _ingest_threat(self, session: AsyncSession, finding: dict):
        """Store threat in threats cell"""
        from itl_braincell_sdk.cells.threats.model import Threat
        
        threat = Threat(
            threat_id=finding["threat_id"],
            threat_name=finding["threat_name"],
            severity=finding["severity"],
            confidence=finding["confidence"],
            detector="amalia:cyber",
            braincell_source="amalia"
        )
        session.add(threat)
    
    async def get_metrics(self) -> dict:
        """Return consumer metrics"""
        return self.metrics
```

#### Lifecycle (in API startup)

```python
# main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    amalia_consumer = AmaliaConsumer(
        redis_url=settings.redis_url,
        db_session_factory=SessionLocal
    )
    consumer_task = asyncio.create_task(amalia_consumer.start())
    
    yield
    
    # Shutdown
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("Amalia consumer stopped")

app = FastAPI(lifespan=lifespan)
```

---

### Phase 3: MCP Tool Exposure (Sprint 5)

**What**: BrainCell exposes Amalia collectors as MCP tools  
**Effort**: 3–4 days  
**Benefit**: Claude agents can autonomously query OSINT/SIGINT/VulnScan

#### New Cell: `amalia_collectors`

**Location**: `ITL.BrainCell/src/cells/amalia_collectors/`

```python
# cell.py
from itl_braincell_sdk.cells.base import MemoryCell
from fastapi import APIRouter, Depends

class AmaliaCollectorsCell(MemoryCell):
    """
    Expose Amalia collector APIs as MCP tools.
    
    Enables Claude agents to:
    - Query OSINT (DNS, WHOIS, SSL, breach DB)
    - Monitor radio frequencies (SIGINT)
    - Scan binaries for vulnerabilities
    - Extract IOCs from threat feeds
    """
    
    name = "amalia_collectors"
    prefix = "/api/amalia"
    
    def __init__(self, amalia_api_url: str = "http://amalia-api:8000"):
        self.amalia_api_url = amalia_api_url
    
    def get_router(self) -> APIRouter:
        """No direct routes; all access via MCP tools"""
        return APIRouter()
    
    def get_models(self):
        """No ORM models; this is a pure integration cell"""
        return []
    
    def register_mcp_tools(self, mcp):
        """Register MCP tool wrappers for Amalia collectors"""
        
        @mcp.tool()
        async def query_osint(
            entity: str,
            entity_type: str = "domain"
        ) -> dict:
            """
            Query 20+ OSINT sources for an entity.
            
            Args:
                entity: Domain, IP, email, or person name
                entity_type: 'domain', 'ip', 'email', 'person'
            
            Returns:
                DNS records, WHOIS data, SSL certs, breach DB hits, social media profiles
            
            Example:
                >>> await query_osint("example.com", "domain")
                {
                    "entity": "example.com",
                    "dns_records": [...],
                    "whois": {...},
                    "ssl_certs": [...],
                    "breach_db": ["Found in 3 breaches"],
                    "sources_queried": ["DNS", "WHOIS", "SSL", "BreachDB", ""]
                }
            """
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.amalia_api_url}/api/collectors/osint/query",
                    params={"entity": entity, "type": entity_type},
                    timeout=30.0
                )
                response.raise_for_status()
            
            return response.json()
        
        @mcp.tool()
        async def query_sigint(
            frequency_khz: int,
            duration_sec: int = 10,
            region: str = None
        ) -> dict:
            """
            Query 127+ WebSDR instances for signal intelligence.
            
            Args:
                frequency_khz: Frequency to monitor (e.g., 121500 for 121.5 MHz)
                duration_sec: Duration to monitor (default 10 sec)
                region: Geographic region for WebSDR selection (optional)
            
            Returns:
                Signal waterfall, frequency trackers, demodulated audio, metadata
            
            Example:
                >>> await query_sigint(121500, duration_sec=30)
                {
                    "frequency_khz": 121500,
                    "duration_sec": 30,
                    "signals_detected": 7,
                    "waterfall_data": [...],
                    "websdr_instances_queried": 12
                }
            """
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.amalia_api_url}/api/radio/realtime/stream",
                    json={
                        "freq_khz": frequency_khz,
                        "duration": duration_sec,
                        "region": region
                    },
                    timeout=duration_sec + 10
                )
                response.raise_for_status()
            
            return response.json()
        
        @mcp.tool()
        async def scan_binary(
            file_path: str,
            analysis_type: str = "full"
        ) -> dict:
            """
            Scan binary for vulnerabilities (SAST + binary analysis).
            
            Args:
                file_path: Path to binary or source file
                analysis_type: 'full' (SAST + gadgets), 'sast', 'rops'
            
            Returns:
                SAST findings, ROP gadgets, exploitability score
            
            Example:
                >>> await scan_binary("/bin/curl", "full")
                {
                    "file": "/bin/curl",
                    "sast_findings": [...],
                    "rop_gadgets": 142,
                    "exploitability_score": 0.72,
                    "cves_matched": [...]
                }
            """
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.amalia_api_url}/api/collectors/vulnscan/binary",
                    json={
                        "file_path": file_path,
                        "analysis_type": analysis_type
                    },
                    timeout=120.0
                )
                response.raise_for_status()
            
            return response.json()
        
        @mcp.tool()
        async def scan_target(
            target: str,
            detectors: list = None
        ) -> dict:
            """
            Trigger full Amalia threat scan on target.
            
            Args:
                target: IP, domain, or infrastructure identifier
                detectors: List of detectors to use
                    ['cyber', 'physical', 'communication', 'acoustic', 'vulnerability']
            
            Returns:
                Threats detected, IOCs extracted, severity scores
            
            Example:
                >>> await scan_target("192.168.1.1", ["cyber", "vulnerability"])
                {
                    "target": "192.168.1.1",
                    "threats": [...],
                    "iocs": [...],
                    "overall_risk": "HIGH"
                }
            """
            if detectors is None:
                detectors = ["cyber", "vulnerability"]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.amalia_api_url}/api/scan/",
                    json={"target": target, "detectors": detectors},
                    timeout=60.0
                )
                response.raise_for_status()
            
            return response.json()

cell = AmaliaCollectorsCell()
```

#### Usage from Claude

```
User: Can you investigate the domain "evil.example.com"?

Claude (internally):
  1. Call query_osint("evil.example.com", "domain")
     → Returns: DNS records, WHOIS data, SSL certs, breach DB hits
  
  2. Store results in BrainCell osint_findings cell
  
  3. If domain resolves to IP 192.168.1.1:
     Call scan_target("192.168.1.1", ["cyber", "vulnerability"])
     → Returns: Active threats, vulnerabilities
  
  4. Extract IOCs and store in iocs cell
  
  5. Generate report from all findings
```

---

## Finding Storage Mapping

### Where Each Finding Type Gets Stored

| Amalia Finding | Cell(s) | Reason | Status |
|---|---|---|---|
| **Cyber threat** (malware, ransomware, APT) | `threats` (SDK) | Track active threat actors | ✅ Impl |
| **Confirmed vulnerability + PoC** | `vuln_reports` (Security) | Master vulnerability record | ✅ Impl |
| **Before/after patch code** | `vuln_patches` (Security) | Training data for triage ML | ✅ Impl |
| **Supply chain cascade** | `incidents` (SDK) | Show how 1 vuln affects 100+ repos | ✅ Impl |
| **IOCs** (IPs, domains, hashes, URLs) | `iocs` (SDK) | Threat intelligence feeds | ✅ Impl |
| **AI reasoning steps** | `decisions` (SDK) | Explainability: why was this prioritized? | ✅ Impl |
| **Low-confidence findings** | `low_confidence_findings` (Security) | Ensemble voting, model improvement | ✅ Impl |
| **OSINT findings** (DNS, WHOIS, SSL, breach DB) | `infrastructure_analysis` (NEW) | Asset inventory, recon data | ⏳ Sprint 4 |
| **ADS-B/FlightRadar24 signals** | `sigint_collection` (NEW) | Aircraft tracking, pattern analysis | ⏳ Sprint 4 |
| **Radio frequency signals** | `sigint_collection` (NEW) | WebSDR monitoring, frequency intel | ⏳ Sprint 4 |
| **Acoustic events** (gunshots, explosions) | `acoustic_threats` (NEW) | Threat detection from sound classification | ⏳ Sprint 4 |
| **Dark web monitoring** | `threat_intelligence` (NEW) | Leaked data, ransomware negotiations | ⏳ Sprint 4 |
| **Blockchain analysis** (ransomware wallets) | `finint_collection` (NEW) | Money trail tracking | ⏳ Sprint 4 |

---

## Implementation Guide

### Step 1: Ensure Sprint 1 Auth is Complete

Before starting Phase 1 ingest, verify these files exist:

```bash
ITL.BrainCell.Api/src/auth/keycloak.py       # JWT validation
ITL.BrainCell.Api/src/auth/permissions.py    # require_role("itl-cell-writer")
ITL.BrainCell.Api/src/tenant/context.py      # TenantContext
```

### Step 2: Deploy Phase 1 (Synchronous)

```bash
# In ITL.BrainCell.Api repo:
git checkout -b feature/amalia-ingest
cp src/api/routes/ingest.py.template src/api/routes/ingest.py
# Edit with Amalia endpoints from this guide

# Add to main.py router mounting:
app.include_router(ingest_router)

# Test locally:
pytest tests/test_ingest_amalia.py

# Create PR → merge to develop → cherry-pick to release/v0.2
```

### Step 3: Deploy Phase 2 (Async Consumer)

```bash
# Add redis service to docker-compose.yml:
services:
  redis:
    image: redis:7-alpine
    ports:
      - "9503:6379"

# Add consumer to API lifespan:
# See Phase 2 implementation above

# Test high-throughput ingestion:
pytest tests/test_amalia_consumer.py -k "high_throughput"
```

### Step 4: Deploy Phase 3 (MCP Tools)

```bash
# Create new cell:
mkdir -p ITL.BrainCell/src/cells/amalia_collectors
cp docs/10-AMALIA-INTEGRATION.md::AmaliaCollectorsCell src/cells/amalia_collectors/cell.py

# Register cell (auto-discovery picks it up):
# Just ensure __init__.py exports: from .cell import cell

# Test with Claude:
# Start local MCP server, query osint/sigint/vulnscan tools
```

---

## Quick Wins

### 1. Local JSON Cache (Can start TODAY)

Amalia exports findings to local cache (no API required):

```python
# amalia/src/exporters/braincell_cache_exporter.py
import json
from pathlib import Path
from datetime import datetime

class BrainCellCacheExporter:
    """Export Amalia findings to ~/.itl/braincell-cache/"""
    
    def __init__(self):
        self.cache_dir = Path.home() / ".itl" / "braincell-cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_findings(self, findings: list, detector_type: str):
        """Export to bc-amalia-{detector_type}-YYYY-MM-DD.json"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"bc-amalia-{detector_type}-{timestamp}.json"
        
        payload = {
            "detector_type": detector_type,
            "finding_count": len(findings),
            "timestamp": datetime.utcnow().isoformat(),
            "findings": findings
        }
        
        filepath = self.cache_dir / filename
        with open(filepath, "w") as f:
            json.dump(payload, f, indent=2)
        
        logger.info(f"Exported {len(findings)} findings to {filepath}")
```

Usage:
```bash
cd ~/.itl/braincell-cache
ls bc-amalia-*.json    # See exported findings
cat bc-amalia-cyber-2026-08-04_120000.json | jq '.findings[0]'
```

### 2. Ingest Cache into BrainCell (Weekly)

```bash
#!/bin/bash
# scripts/sync-amalia-cache-to-braincell.sh

for file in ~/.itl/braincell-cache/bc-amalia-*.json; do
    echo "Ingesting $file ..."
    curl -X POST http://localhost:9504/api/ingest/amalia/findings \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json" \
        -d @"$file"
done
```

Schedule via cron:
```bash
0 2 * * 0 /path/to/sync-amalia-cache-to-braincell.sh    # Every Sunday 2 AM
```

### 3. CSV Export from Amalia

```bash
amalia export --format csv --output findings-$(date +%Y-%m-%d).csv
# Output: findings-2026-08-04.csv with columns: threat_id, severity, confidence, detector_type
```

Then bulk-import:
```python
import pandas as pd

df = pd.read_csv("findings-2026-08-04.csv")
for _, row in df.iterrows():
    # POST to /api/ingest/amalia/threats
    ...
```

---

## Security Considerations

### Authentication & Authorization

```python
# All ingest endpoints require:
1. Valid JWT token (from Keycloak realm=itl, client=itl-braincell)
2. Role: itl-cell-writer (or itl-cell-admin)
3. Tenant isolation: findings tagged with tenant_id
```

### Data Isolation

```python
# Multi-tenant enforcement:
- Every finding includes tenant_id
- Query filters: WHERE tenant_id = current_tenant
- No cross-tenant data leakage
```

### Rate Limiting

```python
# Redis consumer processes:
- 100 findings/sec per detector type
- Backpressure: queue depth monitored
- Alert if queue exceeds 10,000 messages
```

### Audit Trail

```python
# Every ingest logged:
- audit_logs cell stores:
  - timestamp
  - detector_type
  - finding_count
  - ingested_by (user)
  - source_ip
  - status (success/error)
```

### Network Security

```
Amalia API (port 8000)  →  BrainCell API (port 9504)
                            ↓
                        TLS 1.3 + mTLS (cert-based)
                            ↓
                        Service account auth
                        (not user JWT)
```

---

## FAQ & Troubleshooting

### Q: What if Amalia API is unreachable?

**A**: Phase 2 (Redis queue) solves this. Amalia emits to Redis; BrainCell consumes asynchronously.

If Redis is also down, use Phase 1 quick win: cache findings locally to `~/.itl/braincell-cache/`, then ingest when API recovers.

### Q: How do we handle duplicate findings?

**A**: Each finding has unique `threat_id` or `vuln_id`. BrainCell uses upsert:

```python
# Pseudo-code
existing = await session.get(Threat, threat_id=finding["threat_id"])
if existing:
    existing.update(finding)  # Update confidence, timestamps
else:
    session.add(Threat(**finding))  # Insert new
```

### Q: Can agents query Amalia while ingest is running?

**A**: Yes! Phase 3 MCP tools call Amalia API directly; ingest runs in parallel (Redis consumer).

No contention or blocking.

### Q: What about historical Amalia data?

**A**: Amalia has no persistent storage (until BrainCell integration). Starting ingest:
1. Backfill from Amalia in-memory cache (if still running)
2. Use `amalia export` to dump all findings to CSV
3. Bulk-import via ingest endpoint
4. Going forward, all new findings → BrainCell in real-time

### Q: How many fields does each finding have?

**A**: Varies by detector type:
- **Cyber threat**: 8 fields (threat_id, name, severity, confidence, iocs, tactics, metadata, timestamp)
- **Vulnerability**: 10 fields (vuln_id, cwe, cvss, poc, file, line, chain, type, metadata, timestamp)
- **IOC**: 4 fields (value, type, source, confidence)

See schema examples in Phase 1 section above.

### Q: Can we ingest findings from multiple Amalia instances?

**A**: Yes! Add `source_instance: "amalia-prod"` field to each finding, then route:

```python
if finding.get("source_instance") == "amalia-prod":
    # Tag findings accordingly
elif finding.get("source_instance") == "amalia-dev":
    # Dev findings go to dev BrainCell tenant
```

---

## Next Steps

### Immediate (Next 1 week)

- [ ] Review this document with team
- [ ] Confirm Sprint 1 auth is complete
- [ ] Set up local Redis for testing

### Sprint 3 (Next 2–3 weeks)

- [ ] Implement Phase 1 ingest endpoints
- [ ] Write tests (happy path + error cases)
- [ ] Manual testing with curl
- [ ] Deploy to staging

### Sprint 4 (3–4 weeks out)

- [ ] Implement Redis consumer (Phase 2)
- [ ] Load testing (1000 findings/sec)
- [ ] Implement infrastructure_analysis, sigint_collection cells

### Sprint 5 (4–5 weeks out)

- [ ] Implement MCP cell wrapper (Phase 3)
- [ ] Agent testing (have Claude query OSINT/SIGINT)
- [ ] Production deployment

---

## References

- **Amalia API Docs**: [ITL.Amalia/docs/api.md](../../../ITL.Amalia/docs/api.md)
- **Amalia Agents**: [ITL.Amalia/docs/AGENTS_ARCHITECTURE_OVERVIEW.md](../../../ITL.Amalia/docs/AGENTS_ARCHITECTURE_OVERVIEW.md)
- **BrainCell Architecture**: [02-ARCHITECTURE.md](02-ARCHITECTURE.md)
- **BrainCell Cell Development**: [03-PLUGIN-DEVELOPMENT.md](03-PLUGIN-DEVELOPMENT.md)
- **MCP Integration**: [ITL.BrainCell.Mcp/docs/GUIDE.md](../../../ITL.BrainCell.Mcp/docs/GUIDE.md)

---

**Status**: Ready for Sprint 3–5 implementation planning  
**Approval**: [Pending team review]  
**Last Updated**: 2026-08-04
