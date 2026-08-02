# API Reference

Complete reference for all BrainCell SDK APIs.

## Core APIs

### Settings & Configuration

```python
from itl_braincell_sdk.core import get_settings, Settings

# Get configured settings
settings = get_settings()

# Access configuration
print(settings.database_url)
print(settings.weaviate_url)
print(settings.log_level)
```

**Settings class:**
```python
class Settings(BaseSettings):
    database_url: str  # PostgreSQL async connection string
    weaviate_url: str = "http://localhost:8080"
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 9504
```

### Database

```python
from itl_braincell_sdk.core import (
    get_async_db,
    AsyncSessionLocal,
    init_db,
    Base
)

# Get database session (dependency injection)
async def my_handler(db = Depends(get_async_db)):
    result = await db.execute(select(Model))

# Create session manually
async with AsyncSessionLocal() as session:
    result = await session.execute(select(Model))

# Initialize database (create tables)
await init_db()

# Base metadata (all registered models)
from sqlalchemy import inspect
print(inspect(Base.metadata))
```

---

## Cell APIs

### Memory Cell

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
        """API prefix for routes."""
        return "/api/my-cell"
    
    def get_router(self) -> APIRouter:
        """Return FastAPI router."""
        router = APIRouter()
        # Add routes here
        return router
    
    def get_models(self):
        """Import ORM models (auto-registers)."""
        from .model import MyModel  # noqa
    
    def register_mcp_tools(self, mcp):
        """Register MCP tools for AI agents."""
        @mcp.tool()
        async def my_tool() -> str:
            return "result"
```

### Cell Discovery

```python
from itl_braincell_sdk.cells import discover_cells

# Get all cells (SDK only)
cells = discover_cells()

# Get all cells (SDK + plugins)
cells = discover_cells(include_plugins=True)

# Iterate
for cell in cells:
    print(f"Cell: {cell.name}")
    print(f"  Prefix: {cell.prefix}")
    router = cell.get_router()
    cell.get_models()
    cell.register_mcp_tools(mcp)
```

---

## Plugin APIs

### CellCollectionPlugin

```python
from itl_braincell_sdk.plugins import (
    CellCollectionPlugin,
    PluginConfig,
    PluginMetadata
)

class MyPlugin(CellCollectionPlugin):
    @property
    def name(self) -> str:
        """Plugin name."""
        return "myplugin"
    
    @property
    def description(self) -> str:
        """Plugin description."""
        return "My awesome plugin"
    
    @property
    def config_class(self):
        """Configuration class."""
        return MyPluginConfig
    
    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata."""
        return PluginMetadata(
            name="myplugin",
            version="0.1.0",
            api_version="1.0",
            requires_plugins=[]
        )
    
    def get_cells(self) -> list[MemoryCell]:
        """Return cells provided by plugin."""
        return []
    
    async def on_install(self) -> None:
        """Called on startup."""
        pass
    
    async def on_uninstall(self) -> None:
        """Called on shutdown."""
        pass
    
    async def health_check(self) -> bool:
        """Verify dependencies available."""
        return True
    
    async def get_metrics(self) -> dict:
        """Return plugin metrics."""
        return {}
    
    def get_config(self) -> PluginConfig:
        """Get plugin configuration."""
        return self.config_class()
```

### PluginConfig

```python
from pydantic_settings import BaseSettings
from itl_braincell_sdk.plugins import PluginConfig

class MyPluginConfig(PluginConfig):
    """Environment-driven configuration."""
    
    api_url: str = "https://api.example.com"
    api_key: str = ""
    timeout_seconds: int = 30
    
    class Config:
        env_prefix = "BRAINCELL_MYPLUGIN_"

# Usage:
config = MyPluginConfig()  # Loads from BRAINCELL_MYPLUGIN_* env vars
```

### PluginMetadata

```python
from itl_braincell_sdk.plugins import PluginMetadata

metadata = PluginMetadata(
    name="myplugin",
    version="0.1.0",
    api_version="1.0",
    requires_plugins=["architecture"]  # Optional dependencies
)
```

### Plugin Discovery

```python
from itl_braincell_sdk.cells import discover_cell_plugins

# Get all plugins
plugins = discover_cell_plugins()

# Iterate
for plugin in plugins:
    print(f"Plugin: {plugin.name}")
    cells = plugin.get_cells()
    config = plugin.get_config()
```

### Plugin Bundles

```python
from itl_braincell_sdk.plugins import (
    PluginBundle,
    get_bundle,
    list_bundles,
    install_bundle
)

# List available bundles
bundles = list_bundles()  # ["security-ops", "full-stack", "codebase-intel"]

# Get bundle
bundle = get_bundle("security-ops")
print(bundle.plugins)  # ["security", "operations", "architecture"]

# Install bundle
install_bundle("full-stack")  # Installs all plugins in bundle
```

### Hot Reload

```python
from itl_braincell_sdk.plugins.hot_reload import HotReloadManager

manager = HotReloadManager()

# Reload specific plugin
await manager.reload_plugin("security")

# Reload all plugins
await manager.reload_all_plugins()

# Reload all cells
await manager.reload_cells()

# Get status
status = await manager.get_status()
```

---

## Service APIs

### Weaviate Service

```python
from itl_braincell_sdk.services.weaviate_service import WeaviateService

weaviate = WeaviateService()

# Create collection
await weaviate.create_collection("threats")

# Add document
await weaviate.add_document(
    collection="threats",
    document_id="threat-123",
    content="Threat description",
    metadata={"severity": "high"}
)

# Search
results = await weaviate.search(
    collection="threats",
    query="ransomware",
    limit=10
)
```

### Search Service

Unified search API supporting semantic search, hybrid search, and intelligent reranking across all cell types.

```python
from itl_braincell_sdk.services.search_service import SearchService

search = SearchService()

# Semantic search (vector embeddings)
semantic_results = await search.semantic_search(
    query="ransomware attack",
    cell_types=["threats", "incidents"],
    limit=10
)

# Hybrid search (semantic + keyword)
hybrid_results = await search.hybrid_search(
    query="critical vulnerability",
    cell_types=["threats", "codebase"],
    semantic_weight=0.6,  # 60% semantic, 40% keyword
    limit=10
)

# Search with intelligent reranking
reranked = await search.search_with_reranking(
    query="authentication bypass",
    cell_types=["threats", "architecture"],
    limit=5,
    rerank_model="cross-encoder"  # Advanced reranking
)
```

### Sync Service

```python
from itl_braincell_sdk.services.sync_service import SyncService

sync = SyncService()

# Sync data across cells
await sync.sync_cell_data(
    source_cell="threats",
    target_cell="incidents"
)
```

### Search Service (Roadmap)

The `SearchService` provides unified search with semantic, hybrid, and reranking capabilities. **Currently in development as part of RAG enhancement.**

```python
# Future API (not yet implemented)
from itl_braincell_sdk.services.search_service import SearchService

search = SearchService()

# Semantic search (vector embeddings)
semantic_results = await search.semantic_search(
    query="ransomware attack",
    cell_types=["threats", "incidents"],
    limit=10
)

# Hybrid search (semantic + keyword)
hybrid_results = await search.hybrid_search(
    query="critical vulnerability",
    cell_types=["threats", "codebase"],
    semantic_weight=0.6,  # 60% semantic, 40% keyword
    limit=10
)

# Search with intelligent reranking
reranked = await search.search_with_reranking(
    query="authentication bypass",
    cell_types=["threats", "architecture"],
    limit=5,
    rerank_model="cross-encoder"  # Advanced reranking
)
```

See [AI Knowledge Systems](../docs/08-AI-KNOWLEDGE-SYSTEMS.md) for implementation roadmap and phase schedule.

```python
from itl_braincell_sdk.services.retention_policy import RetentionPolicyService

retention = RetentionPolicyService()

# Clean up old data
await retention.cleanup_old_records(
    table="threats",
    days_old=90
)
```

---

## FastAPI Integration

### Using Cells in FastAPI

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from itl_braincell_sdk.cells import discover_cells

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    cells = discover_cells(include_plugins=True)
    for cell in cells:
        router = cell.get_router()
        app.include_router(router, prefix=cell.prefix)
    
    yield
    
    # Shutdown

app = FastAPI(lifespan=lifespan)
```

### Dependency Injection

```python
from fastapi import Depends
from itl_braincell_sdk.core import get_async_db

@app.get("/items")
async def list_items(db = Depends(get_async_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

---

## ORM & Schemas

### Base Model

```python
from itl_braincell_sdk.core.models import Base
from sqlalchemy import Column, Integer, String

class MyModel(Base):
    __tablename__ = "my_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    # All models auto-register with Base.metadata
```

### Pydantic Schemas

```python
from pydantic import BaseModel, Field

class MySchema(BaseModel):
    """Response schema."""
    id: int
    name: str = Field(..., min_length=1, max_length=255)
    
    class Config:
        from_attributes = True  # Pydantic v2
```

---

## Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

**Enable debug logging:**
```bash
export BRAINCELL_LOG_LEVEL=DEBUG
export LOG_LEVEL=DEBUG
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BRAINCELL_DATABASE_URL` | Required | PostgreSQL async URL |
| `BRAINCELL_WEAVIATE_URL` | `http://localhost:8080` | Weaviate endpoint |
| `BRAINCELL_REDIS_URL` | `redis://localhost:6379` | Redis endpoint |
| `BRAINCELL_LOG_LEVEL` | `INFO` | Logging level |
| `BRAINCELL_API_HOST` | `0.0.0.0` | API host |
| `BRAINCELL_API_PORT` | `9504` | API port |

---

## Common Patterns

### Async Database Query

```python
from sqlalchemy import select
from itl_braincell_sdk.core import AsyncSessionLocal

async def get_all_items():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Item))
        return result.scalars().all()
```

### Create and Commit

```python
async def create_item(item_data):
    async with AsyncSessionLocal() as session:
        item = Item(**item_data)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item
```

### Query with Filter

```python
async def get_active_items():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Item).where(Item.status == "active")
        )
        return result.scalars().all()
```

### FastAPI Route Handler

```python
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/{item_id}")
async def get_item(item_id: int):
    async with AsyncSessionLocal() as session:
        item = await session.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404)
        return item

@router.post("")
async def create_item(data: ItemCreate):
    async with AsyncSessionLocal() as session:
        item = Item(**data.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item
```

---

## Summary

| Component | Module | Key Classes |
|-----------|--------|------------|
| **Configuration** | `core` | `Settings`, `get_settings()` |
| **Database** | `core` | `AsyncSessionLocal`, `Base` |
| **Cells** | `cells` | `MemoryCell`, `discover_cells()` |
| **Plugins** | `plugins` | `CellCollectionPlugin`, `discover_cell_plugins()` |
| **Configuration** | `plugins` | `PluginConfig`, `PluginMetadata` |
| **Bundles** | `plugins` | `PluginBundle`, `install_bundle()` |
| **Hot Reload** | `plugins` | `HotReloadManager` |
| **Weaviate** | `services` | `WeaviateService` |
| **Sync** | `services` | `SyncService` |
| **Retention** | `services` | `RetentionPolicyService` |

**Next:** [Deployment](05-DEPLOYMENT.md)
