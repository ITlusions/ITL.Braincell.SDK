# System Architecture & Advanced Features

Deep dive into BrainCell SDK design, automatic model discovery, and advanced plugin capabilities.

**Table of Contents:**
1. [System Design](#system-design)
2. [Cell Discovery](#cell-discovery)
3. [Plugin Discovery](#plugin-discovery)
4. [Automatic Model Discovery](#automatic-model-discovery)
5. [Advanced Plugin Features](#advanced-plugin-features)

---

## System Design

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────┐
│              API/MCP Server Startup                      │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│ 1. Load Configuration (Pydantic BaseSettings)            │
│    - Read environment variables                          │
│    - Validate settings                                   │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│ 2. Connect to Database                                   │
│    - Create async SQLAlchemy engine                      │
│    - Initialize connection pool                          │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│ 3. Discover Cells (SDK + Plugins)                        │
│    - Scan cells/ folder                                  │
│    - Load entry points from installed plugins            │
│    - Instantiate MemoryCell objects                      │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│ 4. Discover Models (Automatic)                           │
│    - Call cell.get_models() for each cell               │
│    - Models self-register with Base.metadata            │
│    - Build complete schema registry                      │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│ 5. Run Database Migrations (Alembic)                     │
│    - Compare Base.metadata vs. database schema          │
│    - Generate migration if needed                        │
│    - Apply migration to database                         │
│    - Create/update tables                                │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│ 6. Discover Plugins (Meta-layer)                         │
│    - Load CellCollectionPlugin instances                │
│    - Validate plugin dependencies                        │
│    - Skip plugins with unmet dependencies                │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│ 7. Initialize Plugins (Lifecycle)                        │
│    - Call plugin.on_install() for each                  │
│    - Call plugin.health_check() for each                │
│    - Collect plugin.get_metrics() for logging            │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│ 8. Register API Routes                                   │
│    - Mount cell routers at /api/<prefix>                │
│    - Mount admin endpoints                               │
│    - Ready to handle requests                            │
└──────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────┐
│ 9. Register MCP Tools                                    │
│    - Call cell.register_mcp_tools() for each            │
│    - Tools become callable by Claude/AI agents           │
│    - Ready for AI integration                            │
└──────────────────────────────────────────────────────────┘
    ↓
Server Running ✓
```

### Concurrency Model

**Async-first architecture:**

```python
# All database operations are async
async with AsyncSessionLocal() as session:
    result = await session.execute(select(Model))

# API handlers are async
@app.get("/items")
async def list_items(db = Depends(get_db)):
    return await db.execute(select(Item))

# Plugin hooks are async
async def on_install(self):
    await self.load_external_feeds()
```

**Benefits:**
- ✅ Non-blocking I/O
- ✅ Scales to thousands of concurrent requests
- ✅ Integrates seamlessly with FastAPI/Starlette
- ✅ Database connection pooling

---

## Cell Discovery

### Mechanism

**Cell Discovery** finds all `MemoryCell` implementations available at runtime.

```python
# src/itl_braincell_sdk/cells/__init__.py
def discover_cells(include_plugins: bool = False) -> list[MemoryCell]:
    """
    Discover all available memory cells.
    
    Args:
        include_plugins: If True, also discover cells from plugins.
    
    Returns:
        List of MemoryCell instances (sorted by name).
    """
    cells = []
    
    # 1. Scan SDK cells folder
    for cell_folder in CELLS_DIR.iterdir():
        if cell_folder.is_dir() and cell_folder.name != "__pycache__":
            try:
                # Import cell module
                module = import_module(f"itl_braincell_sdk.cells.{cell_folder.name}")
                cell = module.cell
                cells.append(cell)
            except Exception as e:
                logger.warning(f"Failed to load cell {cell_folder.name}: {e}")
    
    # 2. If requested, also discover plugin cells
    if include_plugins:
        plugins = discover_cell_plugins()
        for plugin in plugins:
            for cell in plugin.get_cells():
                cells.append(cell)
    
    # Return sorted by name
    return sorted(cells, key=lambda c: c.name)
```

### SDK Cells

Built-in cells are in `src/itl_braincell_sdk/cells/`:

```
cells/
├── __pycache__
├── base.py              # MemoryCell ABC
├── __init__.py          # discover_cells(), discover_cell_plugins()
├── conversations/
│   ├── __init__.py      # exports: cell = ConversationsCell()
│   ├── cell.py
│   ├── model.py
│   ├── schema.py
│   └── routes.py
├── notes/
│   └── ... (same structure)
├── snippets/
│   └── ... (same structure)
└── files_discussed/
    └── ... (same structure)
```

**Each cell folder requires:**
- `__init__.py` with `cell = MyCell()` export
- `cell.py` with `MemoryCell` subclass
- `model.py` with SQLAlchemy ORM models
- `schema.py` with Pydantic schemas (optional)
- `routes.py` with FastAPI routes (optional)

### Adding an SDK Cell

```bash
# Create cell directory
mkdir -p src/itl_braincell_sdk/cells/my_new_cell

# Create files
touch src/itl_braincell_sdk/cells/my_new_cell/{__init__,cell,model,schema,routes}.py
```

`cell.py`:
```python
from itl_braincell_sdk.cells import MemoryCell

class MyNewCell(MemoryCell):
    @property
    def name(self) -> str:
        return "my_new"
    
    @property
    def prefix(self) -> str:
        return "/api/my-new"
    
    def get_router(self):
        # ...
    
    def get_models(self):
        from .model import MyNewModel
```

`__init__.py`:
```python
from .cell import MyNewCell

cell = MyNewCell()
```

**Discovery:** Next time `discover_cells()` is called, your cell is automatically included.

---

## Plugin Discovery

### Mechanism

**Plugin Discovery** finds all `CellCollectionPlugin` instances registered via entry points.

```python
# src/itl_braincell_sdk/cells/__init__.py
def discover_cell_plugins() -> list[CellCollectionPlugin]:
    """
    Discover all installed cell collection plugins.
    
    Returns:
        List of CellCollectionPlugin instances (with dependencies validated).
    """
    plugins_by_name = {}
    
    # 1. Load all plugins from entry points
    try:
        entry_points = importlib.metadata.entry_points()
        group = entry_points.select(group=CELL_PLUGIN_ENTRY_POINT_GROUP)
        
        for ep in group:
            try:
                # Load the entry point (factory or instance)
                obj = ep.load()
                
                # If it's a callable, call it
                if callable(obj):
                    plugin = obj()
                else:
                    plugin = obj
                
                # If it's a list/iterable, wrap it
                if not isinstance(plugin, CellCollectionPlugin):
                    # Assume it's a list of cells
                    plugin = IterableCellPlugin(plugin)
                
                plugins_by_name[plugin.name] = plugin
                logger.info(f"✓ Loaded plugin: {plugin.name}")
            
            except Exception as e:
                logger.error(f"Failed to load plugin {ep.name}: {e}")
    
    except Exception as e:
        logger.warning(f"Error loading entry points: {e}")
    
    # 2. Validate dependencies (two-pass discovery)
    return validate_plugin_dependencies(plugins_by_name)
```

### Entry Point Registration

**In plugin's `pyproject.toml`:**

```toml
[project]
name = "itl-braincell-cells-security"
version = "0.1.0"

# ... other config ...

[project.entry-points."itl_braincell_sdk.cell_plugins"]
security = "itl_braincell_cells_security.cells:plugin"
```

**Entry point target options:**

```python
# Option 1: Plugin instance
# itl_braincell_cells_security/cells/__init__.py
plugin = SecurityPlugin()  # Direct instance

# Option 2: Plugin factory function
# itl_braincell_cells_security/cells/__init__.py
def plugin():  # Callable returns plugin
    return SecurityPlugin()

# Option 3: Iterable of cells (auto-wrapped)
# itl_braincell_cells_security/cells/__init__.py
plugin = [ThreatsCell(), IncidentsCell()]  # List of cells
```

### Plugin Dependency Validation

**Two-pass plugin discovery:**

```
Pass 1: Load all plugins
    ├── Load from entry points
    ├── Instantiate plugin objects
    └── Store in plugins_by_name dict

Pass 2: Validate dependencies
    ├── For each plugin:
    │   ├── Get required plugin names (metadata.requires_plugins)
    │   ├── Check if all required plugins are loaded
    │   └── If any missing: skip plugin (log warning)
    └── Return validated plugin list
```

**Example:**
```python
# If security requires architecture:
@property
def metadata(self) -> PluginMetadata:
    return PluginMetadata(
        name="security",
        requires_plugins=["architecture"]  # Requires this
    )

# Discovery will:
# 1. Check if "architecture" plugin is installed
# 2. If yes: Load security plugin
# 3. If no: Skip security (log warning)
```

---

## Automatic Model Discovery

### The Problem (Solved)

**Before:** Each plugin's models had to be manually imported in migration files.

```python
# alembic/env.py (OLD - 28 hardcoded imports!)
from itl_braincell_sdk.cells.conversations.model import Conversation
from itl_braincell_sdk.cells.notes.model import Note
from itl_braincell_sdk.cells.snippets.model import Snippet
# ... 25 more imports ...
from itl_braincell_cells_security.cells.threats.model import Threat
from itl_braincell_cells_security.cells.incidents.model import Incident
# ... impossible to maintain!
```

**After:** Models auto-discovered.

```python
# alembic/env.py (NEW - automatic!)
from itl_braincell_sdk.cells import discover_cells

for cell in discover_cells(include_plugins=True):
    try:
        cell.get_models()  # Automatically imports models
    except Exception as e:
        logger.warning(f"Could not load models for {cell.name}: {e}")
```

### How It Works

**1. At Migration Time (Alembic)**

```python
# alembic/env.py
from itl_braincell_sdk.cells import discover_cells

def run_migrations_online() -> None:
    # ... alembic configuration ...
    
    # AUTO-DISCOVER CELL MODELS
    logger.info("Auto-discovering cell models for migrations...")
    cells = discover_cells(include_plugins=True)
    
    for cell in cells:
        try:
            cell.get_models()  # Import cell's ORM models
            logger.info(f"  ✓ Loaded models for cell: {cell.name}")
        except Exception as e:
            logger.warning(f"Could not load models for {cell.name}: {e}")
    
    # Alembic now introspects Base.metadata for all tables
    with connectable.begin() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,  # All models are here!
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

**2. At Startup Time (API/MCP)**

```python
# main.py (FastAPI lifespan startup)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting BrainCell API...")
    
    # Auto-discover and load cell models
    cells = discover_cells(include_plugins=True)
    for cell in cells:
        try:
            cell.get_models()
            logger.info(f"✓ Loaded models for {cell.name}")
        except Exception as e:
            logger.error(f"Failed to load models for {cell.name}: {e}")
    
    # Create tables if they don't exist
    await init_db()
    
    # ... rest of startup ...
    
    yield
    
    # Shutdown
    logger.info("Shutting down BrainCell API...")
```

### Model Registration Mechanism

**SQLAlchemy's declarative system:**

```python
# 1. Define Base (once, in core/models.py)
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# 2. Each model inherits from Base
from itl_braincell_sdk.core.models import Base

class Threat(Base):
    __tablename__ = "threats"
    # ... columns ...

# 3. When model module is imported, the class is automatically registered
#    with Base.metadata (via SQLAlchemy's metaclass system)

# 4. Later, Alembic introspects Base.metadata:
Base.metadata.tables  # Contains: "threats", "incidents", "notes", etc
```

### Benefits

| Benefit | Explanation |
|---------|-------------|
| **No Hardcoding** | No manual imports needed |
| **Scales** | Works with 4 cells or 400 |
| **Plugin-Friendly** | Plugins auto-discovered |
| **Maintainable** | Adding cell = add entry point |
| **Backward Compatible** | Existing migrations still work |
| **Error Isolation** | Failed cells don't crash system |

### Adding a New Model

```python
# plugin/cells/my_cell/model.py
from itl_braincell_sdk.core.models import Base
from sqlalchemy import Column, Integer, String

class MyModel(Base):
    __tablename__ = "my_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    value = Column(String(1000))
```

**What happens next:**
1. Entry point registers cell
2. `discover_cells(include_plugins=True)` finds it
3. `cell.get_models()` imports `my_cell/model.py`
4. SQLAlchemy's metaclass auto-registers `MyModel` with `Base.metadata`
5. Next migration finds the table and creates it
6. Done! ✓ No Alembic changes needed.

### Troubleshooting Model Discovery

**Q: Cell not discovered**
```python
# Verify:
from itl_braincell_sdk.cells import discover_cells
cells = discover_cells(include_plugins=True)
print([c.name for c in cells])

# Check plugin entry point in pyproject.toml:
# [project.entry-points."itl_braincell_sdk.cell_plugins"]
# my_plugin = "my_package.cells:plugin"
```

**Q: Models not registering**
```python
# Verify:
# 1. Model imports from correct Base:
from itl_braincell_sdk.core.models import Base  # ✓ Correct
from sqlalchemy.orm import declarative_base; Base = ...  # ✗ Wrong

# 2. Model inherits from Base:
class MyModel(Base):  # ✓ Correct
    pass

# 3. Model has __tablename__:
class MyModel(Base):
    __tablename__ = "my_table"  # ✓ Required
```

**Q: Migration fails with "Table Already Exists"**
```bash
# Solution: Stamp without running
python -m alembic stamp head

# Docker entrypoint handles this:
if ! alembic upgrade head; then
    alembic stamp head
fi
```

---

## Advanced Plugin Features

### 1. Plugin Configuration

**Environment-driven settings for each plugin:**

```python
# plugin/config.py
from pydantic_settings import BaseSettings

class SecurityPluginConfig(BaseSettings):
    """Load settings from BRAINCELL_SECURITY_* env vars."""
    
    threat_alert_threshold: int = 7
    max_iocs_per_report: int = 1000
    enable_auto_sync: bool = True
    threat_feed_url: str = "https://api.threatstream.com"
    api_timeout_seconds: int = 30
    
    class Config:
        env_prefix = "BRAINCELL_SECURITY_"

# plugin/cells/__init__.py
from itl_braincell_sdk.plugins import CellCollectionPlugin
from ..config import SecurityPluginConfig

class SecurityPlugin(CellCollectionPlugin):
    @property
    def config_class(self):
        return SecurityPluginConfig
    
    def get_cells(self):
        config = self.get_config()  # Load from environment
        return [
            ThreatsCell(config=config),
            IncidentsCell(config=config),
        ]
```

**Set environment variables:**
```bash
export BRAINCELL_SECURITY_THREAT_ALERT_THRESHOLD=8
export BRAINCELL_SECURITY_THREAT_FEED_URL="https://custom.com"
python -m uvicorn main:app
```

**Access configuration:**
```python
# Inside plugin or cell
plugin = discover_cell_plugins()[0]
config = plugin.get_config()
print(config.threat_alert_threshold)  # 8
```

### 2. Lifecycle Hooks

**Initialize/cleanup resources at startup/shutdown:**

```python
class SecurityPlugin(CellCollectionPlugin):
    async def on_install(self):
        """Called on startup or first install."""
        logger.info("Initializing security plugin...")
        
        # Load threat feeds
        self.feeds = await self.load_threat_feeds()
        
        # Initialize cache
        self.cache = await self.init_cache()
        
        # Register webhooks
        await self.register_external_webhooks()
        
        # Seed initial data
        await self.seed_threat_database()
    
    async def on_uninstall(self):
        """Called on shutdown or plugin removal."""
        logger.info("Cleaning up security plugin...")
        
        # Close connections
        await self.close_threat_feed_connections()
        
        # Unregister webhooks
        await self.unregister_webhooks()
        
        # Archive recent data
        await self.archive_old_incidents()
```

**Integrated into API lifespan:**
```python
# main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    plugins = discover_cell_plugins()
    
    for plugin in plugins:
        try:
            await plugin.on_install()
            logger.info(f"✓ Plugin {plugin.name} initialized")
        except Exception as e:
            logger.error(f"✗ Plugin {plugin.name} failed: {e}")
    
    yield
    
    # Shutdown
    for plugin in plugins:
        try:
            await plugin.on_uninstall()
            logger.info(f"✓ Plugin {plugin.name} cleaned up")
        except Exception as e:
            logger.error(f"✗ Plugin {plugin.name} shutdown error: {e}")
```

### 3. Health Checks

**Verify plugin dependencies at startup:**

```python
class SecurityPlugin(CellCollectionPlugin):
    async def health_check(self) -> bool:
        """Check if all dependencies are available."""
        
        # Check threat feeds
        if not await self.check_threat_feeds():
            logger.error("Threat feeds unreachable")
            return False
        
        # Check database connectivity
        if not await self.check_database():
            logger.error("Database unreachable")
            return False
        
        # Check external APIs
        if not await self.check_external_api_keys():
            logger.error("API keys invalid")
            return False
        
        return True
```

**Executed during startup:**
```python
# main.py
for plugin in plugins:
    if await plugin.health_check():
        logger.info(f"✓ Plugin {plugin.name} health check passed")
    else:
        logger.warning(f"⚠️  Plugin {plugin.name} health check failed")
```

### 4. Metrics Collection

**Monitor plugin performance:**

```python
class SecurityPlugin(CellCollectionPlugin):
    async def get_metrics(self) -> dict:
        """Collect metrics for monitoring."""
        return {
            "total_threats": await self.count_threats(),
            "active_incidents": await self.count_active_incidents(),
            "failed_syncs": await self.count_failed_syncs(),
            "last_sync": await self.get_last_sync_time(),
            "feed_status": {
                "threatstream": await self.check_threatstream_feed(),
                "misp": await self.check_misp_feed(),
            },
            "cache_hit_rate": await self.get_cache_hit_rate(),
        }
```

**Accessed via endpoint:**
```bash
curl http://localhost:9504/api/plugins/security/metrics

# Response:
{
    "plugin": "security",
    "metrics": {
        "total_threats": 1247,
        "active_incidents": 23,
        "failed_syncs": 0,
        "last_sync": "2026-08-03T14:30:45Z",
        "feed_status": {
            "threatstream": true,
            "misp": true
        },
        "cache_hit_rate": 0.87
    }
}
```

### 5. Plugin Dependencies

**Declare plugin requirements:**

```python
class SecurityPlugin(CellCollectionPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="security",
            version="0.1.0",
            api_version="1.0",
            requires_plugins=["architecture"]  # Requires architecture plugin
        )
```

**Dependency validation:**
```python
# If security requires architecture but it's not installed:
# 1. Plugin discovery detects missing dependency
# 2. Logs warning: "⚠️  Skipping plugin 'security': requires 'architecture'"
# 3. Security plugin is NOT loaded
# 4. API continues starting (other plugins load)
```

### 6. Plugin Bundles

**Group plugins for easy installation:**

```python
# plugins/bundles.py
from dataclasses import dataclass

@dataclass
class PluginBundle:
    name: str
    description: str
    plugins: list[str]

BUNDLES = {
    "security-ops": PluginBundle(
        name="security-ops",
        description="Security & Operations",
        plugins=["security", "operations", "architecture"]
    ),
    "full-stack": PluginBundle(
        name="full-stack",
        description="Complete BrainCell",
        plugins=["security", "architecture", "codebase", "operations"]
    ),
    "codebase-intel": PluginBundle(
        name="codebase-intel",
        description="Codebase Intelligence",
        plugins=["codebase", "architecture"]
    ),
}

def install_bundle(name: str, dry_run: bool = False):
    """Install all plugins in a bundle."""
    bundle = BUNDLES[name]
    
    for plugin_name in bundle.plugins:
        if dry_run:
            print(f"Would install: {plugin_name}")
        else:
            subprocess.run([
                "pip", "install",
                f"itl-braincell-cells-{plugin_name}"
            ])
```

**Usage:**
```python
from itl_braincell_sdk.plugins import install_bundle

# Install security-ops bundle
install_bundle("security-ops")
# Installs: security, operations, architecture

# Install full-stack
install_bundle("full-stack")
# Installs: all 4 plugins
```

### 7. Hot Reload

**Update plugins without restarting:**

```python
# plugins/hot_reload.py
class HotReloadManager:
    async def reload_plugin(self, plugin_name: str):
        """Reload specific plugin."""
        # 1. Call plugin.on_uninstall()
        # 2. Reload plugin module
        # 3. Call plugin.on_install()
    
    async def reload_all_plugins(self):
        """Reload all plugins."""
        # 1. Call on_uninstall() for each
        # 2. Reload all plugin modules
        # 3. Call on_install() for each
    
    async def reload_cells(self):
        """Reload all cells."""
        # 1. Reload cell modules
        # 2. Re-register routes
```

**FastAPI endpoints:**
```bash
# Reload specific plugin
POST /api/admin/hot-reload/plugins/security

# Reload all plugins
POST /api/admin/hot-reload/plugins

# Reload all cells
POST /api/admin/hot-reload/cells

# Get status
GET /api/admin/hot-reload/status
```

---

## Extension Points

The SDK provides multiple ways to extend functionality:

| Extension | Where | Type | Example |
|-----------|-------|------|---------|
| **Memory Cell** | SDK or plugin | Implement `MemoryCell` | `ThreatsCell` |
| **Plugin** | Separate package | Implement `CellCollectionPlugin` | `ITL.Braincell.Cells.Security` |
| **Service** | `services/` folder | Any class, inject with DI | `WeaviateService` |
| **Configuration** | Plugin's `config.py` | Subclass `PluginConfig` | `SecurityPluginConfig` |
| **Hook** | Plugin class | Async method | `async def on_install(self)` |
| **MCP Tool** | Cell's `register_mcp_tools()` | `@mcp.tool()` decorated | `list_threats()` |
| **API Route** | Cell's `get_router()` | FastAPI `APIRouter` | `GET /api/threats` |

---

## Performance Considerations

### Database Connection Pooling

```python
# core/database.py
engine = create_async_engine(
    database_url,
    echo=False,
    pool_size=20,  # Max connections in pool
    max_overflow=0,  # No additional temporary connections
    pool_pre_ping=True,  # Verify connections before use
)
```

### Query Optimization

```python
# Good: Single query
stmt = select(Threat).filter(Threat.severity > 5).limit(100)

# Bad: N+1 queries
for threat in threats:
    threat.actor = session.execute(
        select(ThreatActor).filter_by(id=threat.actor_id)
    ).scalar()

# Better: Eager load relationships
stmt = select(Threat).options(selectinload(Threat.actor))
```

### Caching Strategy

- Use Redis for frequently-accessed data
- Cache plugin metadata at startup
- Cache cell routes at startup
- Implement TTL for external data

### Async Best Practices

```python
# Good: Concurrent operations
tasks = [
    self.load_threat_feeds(),
    self.init_cache(),
    self.register_webhooks(),
]
await asyncio.gather(*tasks)

# Bad: Sequential operations
await self.load_threat_feeds()
await self.init_cache()
await self.register_webhooks()
```

---

## Summary

| Component | Purpose | Key Classes/Functions |
|-----------|---------|----------------------|
| **Cell Discovery** | Find all MemoryCell implementations | `discover_cells()` |
| **Plugin Discovery** | Find all CellCollectionPlugin instances | `discover_cell_plugins()` |
| **Model Discovery** | Auto-discover models for migrations | Loop in `alembic/env.py` |
| **Lifecycle** | Initialize/cleanup plugins | `on_install()`, `on_uninstall()` |
| **Configuration** | Environment-driven settings | `PluginConfig` |
| **Health Checks** | Verify dependencies | `health_check()` |
| **Metrics** | Monitor performance | `get_metrics()` |
| **Dependencies** | Require other plugins | `metadata.requires_plugins` |
| **Bundles** | Group plugins | `PluginBundle`, `install_bundle()` |
| **Hot Reload** | Update without restart | `HotReloadManager` |

**Next:** [Plugin Development Guide](03-PLUGIN-DEVELOPMENT.md) or [API Reference](04-API-REFERENCE.md)
