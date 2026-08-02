# Plugin Development Guide

Step-by-step guide to building, testing, and publishing BrainCell plugins.

**Table of Contents:**
1. [Quick Start](#quick-start)
2. [Plugin Anatomy](#plugin-anatomy)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Testing](#testing)
5. [Publishing](#publishing)
6. [Examples](#examples)

---

## Quick Start

Create a plugin in 5 minutes:

```bash
# 1. Create project structure
mkdir itl-braincell-cells-myfeature
cd itl-braincell-cells-myfeature

# 2. Create basic structure
mkdir -p src/itl_braincell_cells_myfeature/cells/my_cell

# 3. Create files (shown below)

# 4. Install in editable mode
pip install -e .

# 5. Start using!
```

---

## Plugin Anatomy

### Minimal Plugin Structure

```
itl-braincell-cells-myfeature/
├── pyproject.toml               # Project config + entry point
├── README.md                    # Plugin documentation
├── LICENSE                      # MIT or your license
├── src/
│   └── itl_braincell_cells_myfeature/
│       ├── __init__.py          # Plugin class
│       └── cells/
│           ├── __init__.py      # Exports plugin instance
│           └── my_cell/
│               ├── __init__.py  # Exports: cell = MyCell()
│               ├── cell.py      # MemoryCell subclass
│               ├── model.py     # SQLAlchemy ORM models
│               ├── schema.py    # Pydantic schemas
│               └── routes.py    # FastAPI routes
└── tests/
    ├── conftest.py
    ├── test_my_cell.py
    └── test_plugin.py
```

### Minimal Plugin (`pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "itl-braincell-cells-myfeature"
version = "0.1.0"
description = "My BrainCell plugin"
authors = [{name = "Your Name", email = "you@example.com"}]
requires-python = ">=3.12"
dependencies = [
    "itl-braincell-sdk>=0.1.0",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
]

# CRITICAL: Register plugin via entry point
[project.entry-points."itl_braincell_sdk.cell_plugins"]
myfeature = "itl_braincell_cells_myfeature.cells:plugin"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
]
```

---

## Step-by-Step Guide

### Step 1: Create Plugin Class

**`src/itl_braincell_cells_myfeature/__init__.py`:**

```python
"""My Feature plugin for BrainCell."""
from pydantic_settings import BaseSettings
from itl_braincell_sdk.plugins import CellCollectionPlugin, PluginMetadata

class MyFeaturePluginConfig(BaseSettings):
    """Environment-driven configuration."""
    
    api_url: str = "https://api.example.com"
    api_key: str = ""
    sync_interval_hours: int = 24
    
    class Config:
        env_prefix = "BRAINCELL_MYFEATURE_"

class MyFeaturePlugin(CellCollectionPlugin):
    """My Feature plugin providing domain-specific memory cells."""
    
    @property
    def name(self) -> str:
        return "myfeature"
    
    @property
    def description(self) -> str:
        return "My awesome feature plugin"
    
    @property
    def config_class(self):
        return MyFeaturePluginConfig
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="myfeature",
            version="0.1.0",
            api_version="1.0",
            requires_plugins=[]  # Optional: ["architecture", ...]
        )
    
    def get_cells(self):
        """Return list of memory cells provided by this plugin."""
        from .cells import cell
        return [cell]
    
    async def on_install(self):
        """Initialize plugin (called on startup)."""
        config = self.get_config()
        print(f"Initializing MyFeature plugin...")
        print(f"  API URL: {config.api_url}")
        # Load external data, initialize cache, etc.
    
    async def on_uninstall(self):
        """Cleanup plugin (called on shutdown)."""
        print(f"Cleaning up MyFeature plugin...")
        # Close connections, archive data, etc.
    
    async def health_check(self) -> bool:
        """Verify plugin dependencies are available."""
        config = self.get_config()
        if not config.api_key:
            print("⚠️  MyFeature: API key not configured")
            return False
        return True
    
    async def get_metrics(self) -> dict:
        """Return plugin metrics for monitoring."""
        return {
            "status": "healthy",
            "last_sync": "2026-08-03T14:30:00Z",
        }
```

### Step 2: Create Cell Class

**`src/itl_braincell_cells_myfeature/cells/__init__.py`:**

```python
"""Export plugin instance."""
from ..__init__ import MyFeaturePlugin
from . import my_cell

# Initialize plugin
plugin = MyFeaturePlugin()

__all__ = ["plugin"]
```

**`src/itl_braincell_cells_myfeature/cells/my_cell/__init__.py`:**

```python
"""Export memory cell."""
from .cell import MyFeatureCell

cell = MyFeatureCell()

__all__ = ["cell"]
```

**`src/itl_braincell_cells_myfeature/cells/my_cell/cell.py`:**

```python
"""MyFeature memory cell."""
from fastapi import APIRouter
from itl_braincell_sdk.cells import MemoryCell
from itl_braincell_sdk.core import AsyncSessionLocal
from sqlalchemy import select
from .model import MyFeatureRecord
from .schema import MyFeatureCreate, MyFeatureRead

class MyFeatureCell(MemoryCell):
    """Memory cell for storing MyFeature data."""
    
    @property
    def name(self) -> str:
        return "my_feature"
    
    @property
    def prefix(self) -> str:
        return "/api/my-feature"
    
    def get_router(self) -> APIRouter:
        """Create FastAPI router for cell endpoints."""
        router = APIRouter()
        
        @router.get("")
        async def list_records():
            """List all records."""
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(MyFeatureRecord))
                records = result.scalars().all()
                return [MyFeatureRead.from_orm(r) for r in records]
        
        @router.post("")
        async def create_record(data: MyFeatureCreate):
            """Create new record."""
            async with AsyncSessionLocal() as session:
                record = MyFeatureRecord(**data.model_dump())
                session.add(record)
                await session.commit()
                await session.refresh(record)
                return MyFeatureRead.from_orm(record)
        
        @router.get("/{record_id}")
        async def get_record(record_id: int):
            """Get specific record."""
            async with AsyncSessionLocal() as session:
                record = await session.get(MyFeatureRecord, record_id)
                if not record:
                    return {"error": "Not found"}
                return MyFeatureRead.from_orm(record)
        
        return router
    
    def get_models(self):
        """Import ORM models (auto-registered with Base.metadata)."""
        from .model import MyFeatureRecord  # noqa: F401
    
    def register_mcp_tools(self, mcp):
        """Register MCP tools for Claude integration."""
        
        @mcp.tool()
        async def list_my_feature_records(limit: int = 10) -> str:
            """List recent MyFeature records."""
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(MyFeatureRecord).limit(limit)
                )
                records = result.scalars().all()
                return f"Found {len(records)} records"
        
        @mcp.tool()
        async def create_my_feature_record(name: str, value: str) -> str:
            """Create a new MyFeature record."""
            async with AsyncSessionLocal() as session:
                record = MyFeatureRecord(name=name, value=value)
                session.add(record)
                await session.commit()
                return f"Created record {record.id}"
```

### Step 3: Create ORM Models

**`src/itl_braincell_cells_myfeature/cells/my_cell/model.py`:**

```python
"""SQLAlchemy ORM models for MyFeature cell."""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from itl_braincell_sdk.core.models import Base

class MyFeatureRecord(Base):
    """ORM model for MyFeature records."""
    
    __tablename__ = "myfeature_records"
    
    # Columns
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Status
    status = Column(String(50), default="active", nullable=False)
    
    def __repr__(self):
        return f"<MyFeatureRecord(id={self.id}, name={self.name!r})>"
```

### Step 4: Create Pydantic Schemas

**`src/itl_braincell_cells_myfeature/cells/my_cell/schema.py`:**

```python
"""Pydantic schemas for MyFeature cell."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MyFeatureBase(BaseModel):
    """Base schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    value: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"

class MyFeatureCreate(MyFeatureBase):
    """Schema for creating records."""
    pass

class MyFeatureUpdate(BaseModel):
    """Schema for updating records."""
    name: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class MyFeatureRead(MyFeatureBase):
    """Schema for reading records (with database fields)."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2
```

### Step 5: Create FastAPI Routes (Optional)

**`src/itl_braincell_cells_myfeature/cells/my_cell/routes.py`:**

```python
"""FastAPI routes for MyFeature cell."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from itl_braincell_sdk.core import AsyncSessionLocal
from .model import MyFeatureRecord
from .schema import MyFeatureCreate, MyFeatureUpdate, MyFeatureRead

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("", response_model=list[MyFeatureRead])
async def list_records(db = Depends(get_db)):
    """List all records."""
    result = await db.execute(select(MyFeatureRecord))
    return result.scalars().all()

@router.post("", response_model=MyFeatureRead)
async def create_record(data: MyFeatureCreate, db = Depends(get_db)):
    """Create new record."""
    record = MyFeatureRecord(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record

@router.get("/{record_id}", response_model=MyFeatureRead)
async def get_record(record_id: int, db = Depends(get_db)):
    """Get specific record."""
    record = await db.get(MyFeatureRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    return record

@router.put("/{record_id}", response_model=MyFeatureRead)
async def update_record(
    record_id: int,
    data: MyFeatureUpdate,
    db = Depends(get_db)
):
    """Update record."""
    record = await db.get(MyFeatureRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    
    await db.commit()
    await db.refresh(record)
    return record

@router.delete("/{record_id}")
async def delete_record(record_id: int, db = Depends(get_db)):
    """Delete record."""
    record = await db.get(MyFeatureRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    
    await db.delete(record)
    await db.commit()
    return {"deleted": True}
```

---

## Testing

### Test Setup

**`tests/conftest.py`:**

```python
"""Pytest configuration and fixtures."""
import pytest
from itl_braincell_sdk.core import AsyncSessionLocal

@pytest.fixture
async def db_session():
    """Provide a test database session."""
    async with AsyncSessionLocal() as session:
        yield session
        # Auto-cleanup after test

@pytest.fixture
def plugin():
    """Provide plugin instance."""
    from itl_braincell_cells_myfeature import MyFeaturePlugin
    return MyFeaturePlugin()
```

### Unit Tests

**`tests/test_my_cell.py`:**

```python
"""Tests for MyFeature cell."""
import pytest
from itl_braincell_cells_myfeature.cells.my_cell.model import MyFeatureRecord
from itl_braincell_cells_myfeature.cells.my_cell.schema import MyFeatureCreate

@pytest.mark.asyncio
async def test_create_record(db_session):
    """Test creating a record."""
    record = MyFeatureRecord(
        name="Test Record",
        value="test_value",
        description="A test record"
    )
    db_session.add(record)
    await db_session.commit()
    
    assert record.id is not None
    assert record.name == "Test Record"
    assert record.status == "active"

@pytest.mark.asyncio
async def test_schema_validation():
    """Test Pydantic schema validation."""
    data = MyFeatureCreate(
        name="Valid Record",
        value="test"
    )
    assert data.name == "Valid Record"
    assert data.status == "active"
    
    # Test validation
    with pytest.raises(Exception):  # or ValueError
        MyFeatureCreate(name="")  # Empty name should fail
```

### Plugin Tests

**`tests/test_plugin.py`:**

```python
"""Tests for MyFeature plugin."""
import pytest

@pytest.mark.asyncio
async def test_plugin_lifecycle(plugin):
    """Test plugin lifecycle hooks."""
    await plugin.on_install()
    # Plugin should be ready
    
    health = await plugin.health_check()
    # Note: might fail if API key not set
    
    metrics = await plugin.get_metrics()
    assert "status" in metrics
    
    await plugin.on_uninstall()
    # Plugin should be cleaned up

@pytest.mark.asyncio
async def test_get_cells(plugin):
    """Test cell discovery."""
    cells = plugin.get_cells()
    assert len(cells) > 0
    assert cells[0].name == "my_feature"

def test_plugin_config(plugin):
    """Test configuration loading."""
    config = plugin.config_class()
    # Should load from environment or defaults
    assert config.api_url == "https://api.example.com"
```

### Run Tests

```bash
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_my_cell.py::test_create_record -v

# Run with debug output
pytest -v -s --tb=short
```

---

## Publishing

### PyPI Package

**1. Set up credentials:**

Create `~/.pypirc`:
```ini
[distutils]
index-servers = pypi testpypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-your-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here
```

**2. Build package:**

```bash
pip install build twine

# Build source and wheel
python -m build

# Check package
twine check dist/*
```

**3. Publish to TestPyPI (first):**

```bash
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ itl-braincell-cells-myfeature
```

**4. Publish to PyPI:**

```bash
twine upload dist/*

# Test installation
pip install itl-braincell-cells-myfeature
```

### GitHub Release

```bash
# Create release from tag
gh release create v0.1.0 --title "v0.1.0: Initial release" --notes "First public release"

# Attach wheel file
gh release upload v0.1.0 dist/*.whl
```

---

## Examples

### Example 1: Simple Configuration Plugin

Plugin with environment-driven settings:

```python
# __init__.py
from pydantic_settings import BaseSettings
from itl_braincell_sdk.plugins import CellCollectionPlugin, PluginMetadata

class ConfigPluginConfig(BaseSettings):
    api_endpoint: str
    api_key: str
    
    class Config:
        env_prefix = "BRAINCELL_CONFIG_"

class ConfigPlugin(CellCollectionPlugin):
    @property
    def name(self) -> str:
        return "config"
    
    @property
    def config_class(self):
        return ConfigPluginConfig
    
    def get_cells(self):
        config = self.get_config()
        # Use config to initialize cells
        return [MyConfigCell(api=config.api_endpoint)]

# Usage:
export BRAINCELL_CONFIG_API_ENDPOINT="https://api.example.com"
export BRAINCELL_CONFIG_API_KEY="secret-key"
python -m uvicorn main:app
```

### Example 2: Plugin with External Service Integration

Plugin that syncs with an external API:

```python
# __init__.py
class ExternalSyncPlugin(CellCollectionPlugin):
    async def on_install(self):
        """Initialize sync with external service."""
        config = self.get_config()
        self.client = ExternalServiceClient(
            api_url=config.api_url,
            api_key=config.api_key
        )
        await self.client.authenticate()
        await self.sync_data()
    
    async def on_uninstall(self):
        """Cleanup connections."""
        await self.client.close()
    
    async def health_check(self) -> bool:
        """Verify external service is reachable."""
        return await self.client.ping()
```

### Example 3: Plugin with Plugin Dependencies

Plugin that requires another plugin:

```python
# __init__.py
class AdvancedPlugin(CellCollectionPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="advanced",
            requires_plugins=["base"]  # Requires base plugin
        )
    
    def get_cells(self):
        # If base plugin is installed, we can use its cells
        # If not, this plugin won't load (dependency validation)
        return [AdvancedCell()]
```

---

## Plugin Checklist

Before publishing, ensure:

- ✅ `pyproject.toml` has correct entry point
- ✅ Plugin class extends `CellCollectionPlugin`
- ✅ All cells extend `MemoryCell`
- ✅ Models inherit from SDK's `Base`
- ✅ Schemas use Pydantic v2
- ✅ Configuration uses `BaseSettings` with `env_prefix`
- ✅ All async code works correctly
- ✅ Tests pass (`pytest --cov`)
- ✅ README documents plugin usage
- ✅ LICENSE file present
- ✅ Entry point resolves correctly
- ✅ Plugin discovers in `discover_cell_plugins()`
- ✅ Cells discover in `discover_cells(include_plugins=True)`

---

## Troubleshooting

**Q: Plugin not discovered**
```python
# Check entry point:
from importlib.metadata import entry_points
eps = entry_points(group="itl_braincell_sdk.cell_plugins")
print([ep.name for ep in eps])  # Should list your plugin

# Check plugin can be imported:
from itl_braincell_cells_myfeature.cells import plugin
print(plugin.name)
```

**Q: Cells not discovered from plugin**
```python
# Check get_cells():
plugin = MyPlugin()
cells = plugin.get_cells()
print(len(cells))  # Should be > 0

# Check cell names:
for cell in cells:
    print(f"- {cell.name}")
```

**Q: Models not in database**
```python
# Check models are imported:
for cell in discover_cells(include_plugins=True):
    try:
        cell.get_models()
        print(f"✓ {cell.name}")
    except Exception as e:
        print(f"✗ {cell.name}: {e}")

# Check Base.metadata:
from itl_braincell_sdk.core.models import Base
print(Base.metadata.tables.keys())
```

---

## Summary

✅ Created plugin class (implement `CellCollectionPlugin`)  
✅ Created cell class (implement `MemoryCell`)  
✅ Created ORM models (inherit from SDK `Base`)  
✅ Created Pydantic schemas  
✅ Added FastAPI routes  
✅ Registered entry point in `pyproject.toml`  
✅ Tested plugin  
✅ Published to PyPI  

**Next:** [Examples](07-EXAMPLES/) or [Deployment](05-DEPLOYMENT.md)
