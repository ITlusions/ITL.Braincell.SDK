# Troubleshooting Guide

Common issues and solutions.

## Database Issues

### Connection Error

**Error:**
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**
```bash
# Check database is running
pg_isready -h localhost -p 5432

# Check connection string
echo $BRAINCELL_DATABASE_URL
# Should be: postgresql+asyncpg://user:pass@host:port/dbname

# Test connection
psql -U postgres -d braincell -c "SELECT 1"
```

### Migration Fails

**Error:**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solution:**
```bash
# Check current revision
alembic current

# Show history
alembic history

# Try upgrading
alembic upgrade head

# If table already exists, stamp it
alembic stamp head
```

### Models Not Discovered

**Error:**
```
No tables created when running migrations
```

**Solution:**
```python
# Verify models are imported
from itl_braincell_sdk.cells import discover_cells

cells = discover_cells(include_plugins=True)
for cell in cells:
    try:
        cell.get_models()
        print(f"✓ Loaded {cell.name}")
    except Exception as e:
        print(f"✗ Failed {cell.name}: {e}")

# Check Base.metadata
from itl_braincell_sdk.core.models import Base
print("Tables:", list(Base.metadata.tables.keys()))
```

---

## Plugin Issues

### Plugin Not Discovered

**Error:**
```
Plugin 'myfeature' not found in discover_cell_plugins()
```

**Solution:**
```bash
# Check entry point is registered
from importlib.metadata import entry_points
eps = entry_points(group="itl_braincell_sdk.cell_plugins")
for ep in eps:
    print(f"- {ep.name}: {ep.value}")

# Check pyproject.toml has entry point:
# [project.entry-points."itl_braincell_sdk.cell_plugins"]
# myfeature = "itl_braincell_cells_myfeature.cells:plugin"

# Verify module can be imported
from itl_braincell_cells_myfeature.cells import plugin
print(plugin.name)
```

### Plugin Initialization Fails

**Error:**
```
Plugin myfeature failed: AttributeError: ...
```

**Solution:**
```bash
# Run with debug logging
export BRAINCELL_LOG_LEVEL=DEBUG

# Check plugin config
from itl_braincell_cells_myfeature import MyFeaturePlugin
plugin = MyFeaturePlugin()
config = plugin.get_config()
print(config)

# Check on_install method
import asyncio
asyncio.run(plugin.on_install())
```

### Dependency Validation Fails

**Error:**
```
Plugin 'security' skipped: requires 'architecture'
```

**Solution:**
```bash
# Install missing dependency
pip install itl-braincell-cells-architecture

# Verify both are installed
pip list | grep braincell

# Check they're discoverable
from itl_braincell_sdk.cells import discover_cell_plugins
for p in discover_cell_plugins():
    print(f"- {p.name}")
```

---

## API Issues

### Port Already in Use

**Error:**
```
Address already in use: ('0.0.0.0', 9504)
```

**Solution:**
```bash
# Find process using port
lsof -i :9504

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 9505
```

### Routes Not Registered

**Error:**
```
404 Not Found when accessing /api/threats
```

**Solution:**
```python
# Check cells are discovered
from itl_braincell_sdk.cells import discover_cells
cells = discover_cells(include_plugins=True)
print([c.name for c in cells])

# Check routes are registered in FastAPI
for route in app.routes:
    print(f"{route.path} -> {route.name}")

# Check cell router mounting
from itl_braincell_cells_security.cells.threats import cell
router = cell.get_router()
app.include_router(router, prefix=cell.prefix)
```

---

## Performance Issues

### Slow Database Queries

**Solution:**
```python
# Add indices
from sqlalchemy import Index

class Threat(Base):
    __tablename__ = "threats"
    id = Column(Integer, primary_key=True)
    severity = Column(Integer, index=True)  # Index
    status = Column(String, index=True)  # Index

# Use eager loading
from sqlalchemy.orm import selectinload
result = await session.execute(
    select(Threat).options(selectinload(Threat.actor))
)
```

### High Memory Usage

**Solution:**
```python
# Reduce connection pool
engine = create_async_engine(
    database_url,
    pool_size=10,  # Reduce from 20
)

# Paginate large queries
result = await session.execute(
    select(Threat).limit(100).offset(0)
)
```

### Slow Startup

**Solution:**
```bash
# Profile startup
time python -c "from itl_braincell_sdk.cells import discover_cells; discover_cells(include_plugins=True)"

# Check which cell is slow
import timeit
for cell in cells:
    t = timeit.timeit(lambda: cell.get_models(), number=1)
    print(f"{cell.name}: {t:.2f}s")
```

---

## Logging & Debugging

### Enable Debug Logging

```bash
export BRAINCELL_LOG_LEVEL=DEBUG
export SQLALCHEMY_ECHO=1  # Log all SQL queries
export ASYNCIO_DEBUG=1
```

### Log Levels

| Level | Use Case |
|-------|----------|
| DEBUG | Development, detailed SQL queries |
| INFO | Normal operation |
| WARNING | Deprecated features, degraded performance |
| ERROR | Failures that need attention |
| CRITICAL | System-level failures |

### Debug FastAPI

```python
# Add exception handlers
@app.exception_handler(Exception)
async def exception_handler(request, exc):
    import traceback
    logger.error(traceback.format_exc())
    return {"error": str(exc)}

# Use Debugger
import pdb
pdb.set_trace()  # Stop here
```

---

## Testing

### Test Database Connection

```python
import asyncio
from sqlalchemy import text
from itl_braincell_sdk.core import AsyncSessionLocal

async def test_db():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            print("✓ Database connected")
    except Exception as e:
        print(f"✗ Database error: {e}")

asyncio.run(test_db())
```

### Test Plugin Discovery

```python
from itl_braincell_sdk.cells import discover_cell_plugins

for plugin in discover_cell_plugins():
    print(f"Plugin: {plugin.name}")
    print(f"  Cells: {[c.name for c in plugin.get_cells()]}")
```

### Test Cell Routes

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

response = client.get("/api/threats")
print(response.status_code)
print(response.json())
```

---

## Common Errors

### ImportError: No module named 'itl_braincell_sdk'

**Solution:**
```bash
pip install -e .
# or
pip install itl-braincell-sdk
```

### SyntaxError: Unexpected character after line continuation

**Solution:**
```bash
# Verify Python version
python --version  # Should be 3.12+

# Check syntax
python -m py_compile myfile.py
```

### TypeError: 'async' object is not iterable

**Solution:**
```python
# Use await for async functions
result = await async_function()  # ✓ Correct
result = async_function()  # ✗ Wrong
```

### RuntimeError: Event loop is closed

**Solution:**
```python
# Only create one event loop per test
import asyncio

async def main():
    pass

# ✓ Correct
asyncio.run(main())

# ✗ Wrong
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

---

## Getting Help

1. **Check logs** — Always start with logs
   ```bash
   export BRAINCELL_LOG_LEVEL=DEBUG
   python main.py
   ```

2. **Check this guide** — Use Ctrl+F to search

3. **Test components in isolation**
   ```python
   # Test database
   # Test cell discovery
   # Test plugin loading
   # Test individual cell
   ```

4. **Report issue** — GitHub issues with:
   - Full error message
   - Steps to reproduce
   - Environment (Python version, OS, Docker, etc)
   - Debug logs

---

## Quick Checklist

When something breaks:

- ✓ Check logs: `export BRAINCELL_LOG_LEVEL=DEBUG`
- ✓ Verify database: `psql -U postgres braincell`
- ✓ Verify services: `docker compose ps`
- ✓ Check dependencies: `pip list | grep braincell`
- ✓ Verify environment: `env | grep BRAINCELL`
- ✓ Test cell discovery: `discover_cells()`
- ✓ Test plugin discovery: `discover_cell_plugins()`
- ✓ Restart services: `docker compose restart`

**Next:** Back to [README](README.md) or [Deployment](05-DEPLOYMENT.md)
