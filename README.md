# ITL BrainCell SDK

Shared core library for the BrainCell persistent memory platform. Contains all memory cells, services, data models, and database infrastructure.

## Package Structure

```
src/itl_braincell_sdk/
├── core/                 # Core infrastructure
│   ├── config.py        # Settings management
│   ├── database.py       # Async/sync database engines
│   ├── models.py        # Base ORM models and mixins
│   └── schemas.py       # Shared Pydantic schemas
├── cells/                # Memory cell implementations (28 cells)
│   ├── interactions/
│   ├── conversations/
│   ├── decisions/
│   ├── notes/
│   └── ... (24 more cells)
└── services/             # Cross-cell business logic
    ├── weaviate_service.py   # Vector database integration
    ├── sync_service.py       # Cell synchronization
    └── retention_policy.py   # Data retention management
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

The SDK's Base.metadata includes all 28 cell models automatically via cell discovery.

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
