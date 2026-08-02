# Architecture Overview

Complete guide to BrainCell SDK concepts, system design, and structure.

## What Is BrainCell?

**BrainCell** is a persistent memory platform for organizing, storing, and retrieving domain-specific information. It breaks down data into specialized **memory cells**, each focused on a specific area of knowledge.

### Core Idea

Instead of a single monolithic database, BrainCell uses **domain-driven cell architecture**:

```
Persistent Memory Platform
├── Conversations Cell → Chat history, context, context windows
├── Notes Cell → General observations, annotations
├── Threats Cell → Security threats, incidents, indicators
├── Architecture Cell → Design decisions, architectural notes
├── Codebase Cell → Code analysis, dependencies, errors
├── Operations Cell → Tasks, jobs, runbooks, procedures
└── ... (extend with more cells)
```

Each cell:
- Stores domain-specific data (table, ORM model, API routes)
- Validates data with Pydantic schemas
- Provides REST endpoints
- Can cross-reference other cells
- Contributes to the unified memory system

---

## Key Concepts

### Memory Cell

A **Memory Cell** is a self-contained memory domain with its own:
- **Storage** — SQLAlchemy ORM model(s) and database table(s)
- **Validation** — Pydantic schemas for request/response
- **API** — FastAPI routes for CRUD operations
- **MCP Tools** — Callable functions for Claude/AI agents
- **Metadata** — Name, description, prefix

**Example cell structure:**
```
cells/threats/
├── cell.py          # MemoryCell subclass
├── model.py         # SQLAlchemy models
├── schema.py        # Pydantic schemas
├── routes.py        # FastAPI routes
└── __init__.py      # Exports
```

**Anatomy of a cell:**
```python
from itl_braincell_sdk.cells import MemoryCell

class ThreatsCell(MemoryCell):
    @property
    def name(self) -> str:
        return "threats"
    
    @property
    def prefix(self) -> str:
        return "/api/threats"
    
    def get_router(self):
        # Return FastAPI router
        pass
    
    def get_models(self):
        # Import ORM models (Threat, ThreatActor, etc)
        pass
    
    def register_mcp_tools(self, mcp):
        # Register callable tools for AI agents
        pass

# Export instance
cell = ThreatsCell()
```

### Plugin (Cell Collection)

A **Plugin** is a collection of related cells packaged as a Python package.

**Why plugins?**
- Logically group cells (e.g., "security" cells, "operations" cells)
- Isolate functionality
- Ship as installable packages
- Optional feature sets
- Configuration management per plugin

**Example plugin:**
```
ITL.Braincell.Cells.Security/
├── pyproject.toml       # Entry point registration
├── README.md
├── src/itl_braincell_cells_security/
│   ├── __init__.py      # Plugin class + config
│   ├── config.py        # Environment configuration
│   ├── cells/
│   │   ├── threats/     # Cell 1
│   │   ├── incidents/   # Cell 2
│   │   ├── iocs/        # Cell 3
│   │   └── __init__.py  # SecurityPlugin class
│   └── tests/
```

**Key features:**
- Declares cells it provides
- Has optional configuration
- Declares dependencies on other plugins
- Lifecycle hooks (init/cleanup)
- Health checks
- Metrics collection

**Anatomy of a plugin:**
```python
from itl_braincell_sdk.plugins import (
    CellCollectionPlugin, PluginConfig, PluginMetadata
)

class SecurityPluginConfig(PluginConfig):
    threat_alert_threshold: int = 7
    
    class Config:
        env_prefix = "BRAINCELL_SECURITY_"

class SecurityPlugin(CellCollectionPlugin):
    @property
    def name(self) -> str:
        return "security"
    
    @property
    def config_class(self):
        return SecurityPluginConfig
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="security",
            version="0.1.0",
            requires_plugins=[]  # Optional: require other plugins
        )
    
    def get_cells(self):
        # Return list of MemoryCell instances
        return [ThreatsCell(), IncidentsCell(), ...]
    
    async def on_install(self):
        # Initialize resources (load threat feeds, etc)
        pass
    
    async def on_uninstall(self):
        # Clean up resources
        pass
    
    async def health_check(self) -> bool:
        # Verify all dependencies available
        pass

plugin = SecurityPlugin()
```

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│           REST API / MCP Server                 │
│  (ITL.BrainCell.Api or ITL.BrainCell.Mcp)     │
└─────────────────────────────────────────────────┘
            ↓
            ↓ Uses cells & plugins
            ↓
┌─────────────────────────────────────────────────┐
│        BrainCell SDK (this package)             │
├─────────────────────────────────────────────────┤
│                                                 │
│  Core Infrastructure                           │
│  ├── Database (async SQLAlchemy + PostgreSQL) │
│  ├── Configuration (Pydantic BaseSettings)     │
│  ├── ORM Base Model (shared mixins)           │
│  ├── Schemas (Pydantic v2)                    │
│  └── Services (Weaviate, Sync, Retention)    │
│                                                 │
│  Memory Cells (4 core)                        │
│  ├── conversations/                            │
│  ├── notes/                                    │
│  ├── snippets/                                 │
│  └── files_discussed/                          │
│                                                 │
│  Plugin System                                 │
│  ├── CellCollectionPlugin (ABC)               │
│  ├── Auto-discovery via entry points          │
│  ├── Dependency validation                    │
│  ├── Configuration management                 │
│  ├── Lifecycle hooks                          │
│  ├── Bundle system                            │
│  └── Hot reload system                        │
│                                                 │
└─────────────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────────────┐
│              External Resources                 │
│  ├── PostgreSQL (primary storage)             │
│  ├── Weaviate (vector search)                 │
│  ├── Redis (caching)                          │
│  └── File storage (S3, local, etc)            │
└─────────────────────────────────────────────────┘
```

### Runtime Flow (Startup)

```
API/MCP Server Starts
    ↓
Load Settings
    ↓
Initialize Database Connection
    ↓
Discover Cells (SDK + Plugins)
    ├── Scan cells/ folder
    └── Load entry points from installed plugins
    ↓
Discover Cell Models
    ├── Call cell.get_models() for each cell
    └── Models self-register with Base.metadata
    ↓
Run Database Migrations (if needed)
    ├── Compare Base.metadata vs. database schema
    └── Create/update tables
    ↓
Initialize Plugins
    ├── Call plugin.on_install() for each
    └── Call plugin.health_check() for each
    ↓
Register API Routes
    ├── For each cell, register cell.get_router()
    └── Mount at /api/<cell_prefix>
    ↓
Register MCP Tools
    ├── For each cell, call cell.register_mcp_tools(mcp)
    └── Tools become callable by AI agents
    ↓
Setup Admin Endpoints
    ├── /api/plugins (list plugins)
    ├── /api/plugins/{name}/metrics
    ├── /api/admin/hot-reload/* (manage plugins)
    └── ... (other admin endpoints)
    ↓
Server Ready
```

---

## Folder Structure

### SDK Source

```
src/itl_braincell_sdk/
├── __init__.py              # Package exports
├── core/
│   ├── __init__.py
│   ├── config.py            # Pydantic BaseSettings for configuration
│   ├── database.py          # Async SQLAlchemy engine, session factory
│   ├── models.py            # Base ORM model, common mixins
│   └── schemas.py           # Shared Pydantic schemas
├── cells/
│   ├── __init__.py          # discover_cells(), discover_cell_plugins()
│   ├── base.py              # MemoryCell ABC
│   ├── conversations/
│   │   ├── __init__.py
│   │   ├── cell.py
│   │   ├── model.py
│   │   ├── schema.py
│   │   └── routes.py
│   ├── notes/
│   │   └── ... (same structure)
│   ├── snippets/
│   │   └── ... (same structure)
│   └── files_discussed/
│       └── ... (same structure)
├── plugins/                 # Plugin system infrastructure
│   ├── __init__.py          # Exports all plugin APIs
│   ├── base.py              # CellCollectionPlugin, PluginConfig, PluginMetadata
│   ├── bundles.py           # PluginBundle, plugin bundling/composition
│   └── hot_reload.py        # HotReloadManager, hot reload API
└── services/
    ├── __init__.py
    ├── weaviate_service.py  # Vector database integration
    ├── sync_service.py      # Cross-cell synchronization
    └── retention_policy.py  # Data retention management
```

### Plugin Package Structure (Example)

```
ITL.Braincell.Cells.Security/
├── README.md
├── LICENSE
├── pyproject.toml           # Entry point: [project.entry-points."itl_braincell_sdk.cell_plugins"]
├── Dockerfile
├── docker-compose.yml
├── src/itl_braincell_cells_security/
│   ├── __init__.py          # SecurityPlugin class
│   ├── config.py            # Environment configuration
│   ├── cells/
│   │   ├── __init__.py      # ExportsSecurityPlugin instance
│   │   ├── threats/
│   │   │   ├── __init__.py
│   │   │   ├── cell.py
│   │   │   ├── model.py     # Threat ORM model
│   │   │   ├── schema.py
│   │   │   └── routes.py
│   │   ├── incidents/
│   │   │   └── ... (same structure)
│   │   ├── iocs/
│   │   │   └── ... (same structure)
│   │   └── kill_chains/
│   │       └── ... (same structure)
│   ├── migrations/          # Plugin-specific Alembic versions (optional)
│   └── tests/
│       ├── conftest.py
│       ├── test_threats_cell.py
│       ├── test_incidents_cell.py
│       └── test_plugin.py
├── tests/
└── .gitignore
```

---

## Core Infrastructure

### Database

**SQLAlchemy 2.0 async-first**
- Async drivers (asyncpg for PostgreSQL)
- Non-blocking operations
- Connection pooling
- Type-safe queries

**Base Model:**
```python
# src/core/models.py
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    """Base class for all ORM models."""
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
```

### Configuration

**Pydantic BaseSettings (environment-driven)**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    weaviate_url: str
    redis_url: str
    log_level: str = "INFO"
    
    class Config:
        env_prefix = "BRAINCELL_"
        case_sensitive = False

settings = Settings()  # Loads from env: BRAINCELL_DATABASE_URL, etc
```

### Services

**Core services (current):**
- `WeaviateService` — Vector database backend for semantic search

**Services in Roadmap (RAG enhancement):**
- `SearchService` — Unified search combining multiple strategies
  - **Semantic Search** across all cell types (not yet implemented)
  - **Hybrid Search** combining semantic + keyword matching (not yet implemented)
  - **Intelligent Reranking** for result relevance (not yet implemented)
- `SyncService` — Synchronize data across cells
- `RetentionPolicyService` — Manage data expiration and cleanup

---

## Automatic Model Discovery

The SDK uses **automatic model discovery** for database migrations and startup:

### At Migration Time (Alembic)

```python
# alembic/env.py
from itl_braincell_sdk.cells import discover_cells

for cell in discover_cells(include_plugins=True):
    try:
        cell.get_models()  # Imports cell's ORM models
    except Exception as e:
        logger.warning(f"Could not load models for {cell.name}: {e}")

# Alembic now introspects Base.metadata for all tables
```

### At Startup Time (API/MCP)

```python
# main.py (FastAPI lifespan startup)
from itl_braincell_sdk.cells import discover_cells

async def startup():
    cells = discover_cells(include_plugins=True)
    for cell in cells:
        cell.get_models()  # Import models
    
    init_db()  # Create tables if needed
```

**Benefits:**
- ✅ No hardcoded imports
- ✅ Scales to unlimited cells
- ✅ Plugins auto-discovered
- ✅ Works across SDK and plugin packages

---

## Advanced Plugin Features

### 1. Configuration Management

Each plugin can have environment-driven settings:

```python
from pydantic_settings import BaseSettings

class SecurityPluginConfig(BaseSettings):
    threat_alert_threshold: int = 7
    max_iocs: int = 1000
    auto_sync: bool = True
    
    class Config:
        env_prefix = "BRAINCELL_SECURITY_"

class SecurityPlugin(CellCollectionPlugin):
    @property
    def config_class(self):
        return SecurityPluginConfig
```

Load via: `plugin.get_config()` → reads from `BRAINCELL_SECURITY_*` env vars

### 2. Lifecycle Hooks

Initialize/cleanup resources at startup/shutdown:

```python
async def on_install(self):
    """Called on first install or API startup."""
    await self.load_threat_feeds()
    await self.register_webhooks()

async def on_uninstall(self):
    """Called on shutdown or plugin removal."""
    await self.close_connections()
    await self.unregister_webhooks()

async def health_check(self) -> bool:
    """Verify all dependencies available."""
    return await self.check_threat_feeds_reachable()

async def get_metrics(self) -> dict:
    """Return plugin metrics for monitoring."""
    return {"total_threats": await self.count_threats()}
```

### 3. Plugin Dependencies

Declare that your plugin requires others:

```python
@property
def metadata(self) -> PluginMetadata:
    return PluginMetadata(
        name="security",
        requires_plugins=["architecture"]  # Security requires architecture plugin
    )
```

Validation happens during plugin discovery — unmet dependencies are skipped.

### 4. Plugin Bundles

Group plugins for easy installation:

```python
# Pre-defined bundles:
# - "security-ops" = security + operations + architecture
# - "full-stack" = all plugins
# - "codebase-intel" = codebase + architecture

from itl_braincell_sdk.plugins import install_bundle
install_bundle("security-ops")  # Install 3 plugins at once
```

### 5. Hot Reload

Update plugins without restarting:

```bash
# Reload specific plugin
POST /api/admin/hot-reload/plugins/security

# Reload all plugins
POST /api/admin/hot-reload/plugins

# Get status
GET /api/admin/hot-reload/status
```

---

## Memory Cell Contract

To create a cell, implement the `MemoryCell` ABC:

```python
from itl_braincell_sdk.cells import MemoryCell
from fastapi import APIRouter

class MyCell(MemoryCell):
    @property
    def name(self) -> str:
        """Unique cell name (snake_case)."""
        return "my_cell"
    
    @property
    def prefix(self) -> str:
        """API prefix for routes (e.g., /api/my-cell)."""
        return "/api/my-cell"
    
    def get_router(self) -> APIRouter:
        """Return FastAPI router for this cell's endpoints."""
        router = APIRouter()
        
        @router.get("")
        async def list_items():
            return []
        
        return router
    
    def get_models(self):
        """Import ORM models (they auto-register with Base.metadata)."""
        from .model import MyModel
    
    def register_mcp_tools(self, mcp):
        """Register callable tools for AI agents (Claude)."""
        @mcp.tool()
        async def my_tool() -> str:
            return "Hello from MCP!"

cell = MyCell()
```

---

## Extension Points

The SDK provides multiple extension points:

| Extension | Where | How | Example |
|-----------|-------|-----|---------|
| **New Memory Cell** | SDK or plugin | Implement `MemoryCell` | `ThreatsCell`, `NotesCell` |
| **New Plugin** | Separate package | Create `CellCollectionPlugin` | `ITL.Braincell.Cells.Security` |
| **Custom Service** | `services/` folder | Implement logic, inject with DI | `WeaviateService` |
| **Plugin Configuration** | Plugin's `config.py` | Subclass `PluginConfig` | `SecurityPluginConfig` |
| **Lifecycle Hook** | Plugin class | Override method | `async def on_install(self)` |
| **MCP Tool** | Cell's `register_mcp_tools()` | Use `@mcp.tool()` decorator | `list_threats()` |
| **API Route** | Cell's `get_router()` | FastAPI `APIRouter` | `GET /api/threats` |

---

## Data Flow: Query Example

Example: Get all threats via REST API

```
1. Client: GET /api/threats?status=active
    ↓
2. FastAPI Router
    ↓ Routes to threats cell's router
3. Threats Cell Handler
    ├── Parse query parameters
    ├── Validate with Pydantic schema
    └── Call service layer
    ↓
4. ThreatService (business logic)
    ├── Query database
    ├── Apply filters
    └── Enrich with vector search
    ↓
5. Database (PostgreSQL)
    ├── SELECT * FROM threats WHERE status = 'active'
    └── Return ORM objects
    ↓
6. Response Schema
    ├── Convert ORM objects to Pydantic schemas
    └── Serialize to JSON
    ↓
7. Client receives JSON response
```

---

## Summary

| Concept | Purpose | Key Files |
|---------|---------|-----------|
| **Memory Cell** | Self-contained domain for storing data | `cells/*/cell.py`, `model.py`, `schema.py` |
| **Plugin** | Collection of related cells | `CellCollectionPlugin` in `plugins/base.py` |
| **SDK Core** | Shared infrastructure | `core/config.py`, `core/database.py`, `core/models.py` |
| **Plugin System** | Auto-discovery, config, lifecycle | `plugins/*.py` |
| **Auto Discovery** | Find cells & plugins at runtime | `cells/__init__.py`, `plugins/base.py` |
| **Services** | Cross-cell utilities | `services/*.py` |

**Next:** [Getting Started](01-GETTING-STARTED.md)
