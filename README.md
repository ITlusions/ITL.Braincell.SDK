# ITL BrainCell SDK

Shared core library for the BrainCell persistent memory platform. Contains all memory cells, services, data models, database infrastructure, and the plugin loader for installable cell collections.

**[Full Documentation](docs/README.md)** — Complete guides, examples, API reference, and deployment instructions.

## Package Structure

```
src/itl_braincell_sdk/
├── core/                 # Core infrastructure
│   ├── config.py        # Settings management
│   ├── database.py       # Async/sync database engines
│   ├── models.py        # Base ORM models and mixins
│   └── schemas.py       # Shared Pydantic schemas
├── cells/                # 4 built-in memory cells
│   ├── conversations/    # Chat history & context
│   ├── notes/            # General observations
│   ├── snippets/         # Code & documentation
│   └── files_discussed/  # File references
└── services/             # Cross-cell business logic
    ├── search_service.py         # Semantic, hybrid, reranked search
    ├── weaviate_service.py       # Vector database integration
    ├── sync_service.py           # Cell synchronization
    └── retention_policy.py       # Data retention management
```

## Installation

### Local Development
```bash
pip install -e .
```

### In Docker (from parent directory)
```bash
pip install /path/to/ITL.Braincell.SDK
```

## Documentation

Comprehensive documentation available in `/docs/`:

| Guide | For | Time |
|-------|-----|------|
| [Getting Started](docs/01-GETTING-STARTED.md) | Users & developers | 30 min |
| [Architecture](docs/02-ARCHITECTURE.md) | Understanding the system | 45 min |
| [Plugin Development](docs/03-PLUGIN-DEVELOPMENT.md) | Building plugins | 60 min |
| [API Reference](docs/04-API-REFERENCE.md) | API documentation | Quick ref |
| [Deployment](docs/05-DEPLOYMENT.md) | Production setup | 30 min |
| [Troubleshooting](docs/06-TROUBLESHOOTING.md) | Common issues | On-demand |
| [AI Knowledge Systems](docs/08-AI-KNOWLEDGE-SYSTEMS.md) | Future RAG features | 45 min |
| [RAG Explained](docs/09-RAG-EXPLAINED.md) | Understanding RAG | 30 min |

**Start here:** [docs/README.md](docs/README.md) for navigation by role.

## Usage

### Import Core Infrastructure
```python
from itl_braincell_sdk.core import get_settings, get_async_db, Base
from itl_braincell_sdk.core.database import async_engine, AsyncSessionLocal

async def get_memory():
    async with AsyncSessionLocal() as session:
        # Use session for database operations
        pass
```

### Import Cell Models
```python
from itl_braincell_sdk.cells.conversations.model import Conversation
from itl_braincell_sdk.cells.decisions.model import DesignDecision
```

### Import Services
```python
from itl_braincell_sdk.services.weaviate_service import WeaviateService
from itl_braincell_sdk.services.sync_service import SyncService

weaviate = WeaviateService()
sync = SyncService()
```

## Database Migrations

The SDK provides Base metadata for all cell models. Each service (API, MCP) runs migrations independently but references SDK models.

### Running Migrations
```bash
alembic upgrade head
```

The SDK's Base.metadata includes all built-in cell models automatically, and any installed plugins can add more cells through the discovery loader.

### Install Cell Collection Plugins

External packages can contribute a collection of cells by exposing an entry point in the `itl_braincell_sdk.cell_plugins` group.

Example `pyproject.toml` in a plugin package:

```toml
[project.entry-points."itl_braincell_sdk.cell_plugins"]
my_memory_collection = "my_package.cells:plugin"
```

The entry point can resolve to a `CellCollectionPlugin` instance, a factory that returns one, or a callable that returns an iterable of `MemoryCell` objects.

```python
from itl_braincell_sdk.cells.base import MemoryCell
from itl_braincell_sdk.cells.plugins import CellCollectionPlugin


class MyCollection(CellCollectionPlugin):
    @property
    def name(self) -> str:
        return "my_collection"

    def get_cells(self) -> list[MemoryCell]:
        from my_package.cells.notes.cell import cell as notes_cell
        from my_package.cells.tasks.cell import cell as tasks_cell

        return [notes_cell, tasks_cell]


plugin = MyCollection()
```

## Core Modules

### config.py
- `Settings` — Pydantic BaseSettings with environment variable support
- `get_settings()` — Singleton settings instance

### database.py
- `async_engine` — AsyncIO SQLAlchemy engine for async operations
- `AsyncSessionLocal` — Async session factory
- `get_async_db()` — FastAPI dependency for async sessions
- `get_async_engine()` — Get engine for migrations

### models.py
- `Base` — SQLAlchemy declarative base (all cells register with this)
- `TimestampMixin` — created_at / updated_at timestamp fields
- `RetentionMixin` — Data retention metadata

### schemas.py
- `SearchQuery` — Search request schema
- `SearchResult` — Search result schema
- `schema_to_db_kwargs()` — Convert Pydantic model to ORM kwargs

## Dependencies

- FastAPI >= 0.127.0
- SQLAlchemy >= 2.0.46
- asyncpg >= 0.30.0 (async PostgreSQL driver)
- Pydantic >= 2.12.3
- Weaviate-client >= 4.19.2
- Alembic >= 1.13.0
