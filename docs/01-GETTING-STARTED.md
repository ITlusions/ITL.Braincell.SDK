# Getting Started with BrainCell SDK

A practical guide to installing, setting up, and using the SDK.

## Installation (5 minutes)

### Option 1: Local Development

```bash
# Clone the repository
git clone https://github.com/ITlusions/ITL.Braincell.SDK.git
cd ITL.Braincell.SDK

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .
```

### Option 2: From PyPI

```bash
pip install itl-braincell-sdk
```

### Option 3: In a Docker Container

```dockerfile
FROM python:3.12-slim
RUN pip install itl-braincell-sdk
```

### Verify Installation

```bash
python -c "from itl_braincell_sdk import __version__; print(f'✓ Installed: {__version__}')"
```

---

## First Example: Discover Cells (2 minutes)

List all available memory cells:

```python
from itl_braincell_sdk.cells import discover_cells

# Discover all cells (SDK + plugins)
cells = discover_cells()

print(f"Found {len(cells)} cells:")
for cell in cells:
    print(f"  - {cell.name} ({cell.prefix})")

# Output:
# Found 4 cells:
#   - conversations (/api/conversations)
#   - notes (/api/notes)
#   - snippets (/api/snippets)
#   - files_discussed (/api/files_discussed)
```

---

## Database Setup (5 minutes)

### Prerequisites

- **PostgreSQL 14+** — Install locally or use Docker
- **Environment variables** — Set database URL

### Option 1: Local PostgreSQL

```bash
# Install PostgreSQL (macOS with Homebrew)
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb braincell_dev

# Set environment variable
export BRAINCELL_DATABASE_URL="postgresql+asyncpg://postgres:password@localhost/braincell_dev"
```

### Option 2: Docker PostgreSQL

```bash
docker run -d \
  --name braincell-postgres \
  -e POSTGRES_DB=braincell_dev \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

# Set environment variable
export BRAINCELL_DATABASE_URL="postgresql+asyncpg://postgres:password@localhost/braincell_dev"
```

### Option 3: Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.9'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: braincell_dev
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  weaviate:
    image: semitechnologies/weaviate:latest
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_APIKEY_ENABLED: false
      PERSISTENCE_DATA_PATH: /var/lib/weaviate
    ports:
      - "8080:8080"
    volumes:
      - weaviate_data:/var/lib/weaviate

volumes:
  postgres_data:
  weaviate_data:
```

Start services:

```bash
docker compose up -d

# Set environment variable
export BRAINCELL_DATABASE_URL="postgresql+asyncpg://postgres:password@localhost/braincell_dev"
```

---

## Database Migrations

### Create Initial Schema

The SDK is typically used with Alembic for database migrations. If you're using the BrainCell API:

```bash
cd /path/to/ITL.BrainCell.Api
python -m alembic upgrade head
```

Or run migrations programmatically:

```python
from itl_braincell_sdk.core import init_db

async def main():
    await init_db()  # Creates tables if they don't exist
    print("✓ Database initialized")

# Run it
import asyncio
asyncio.run(main())
```

---

## Second Example: Query Memory

Query the database using async SQLAlchemy:

```python
import asyncio
from itl_braincell_sdk.core import get_async_db
from itl_braincell_sdk.cells.conversations.model import Conversation

async def get_conversations():
    # Get database session
    db = await get_async_db()
    
    # Query conversations
    conversations = await db.execute(
        "SELECT * FROM conversations LIMIT 10"
    )
    
    return conversations

# Run it
asyncio.run(get_conversations())
```

Or use SQLAlchemy ORM:

```python
import asyncio
from sqlalchemy import select
from itl_braincell_sdk.core import AsyncSessionLocal
from itl_braincell_sdk.cells.conversations.model import Conversation

async def get_recent_conversations():
    async with AsyncSessionLocal() as session:
        # ORM query
        result = await session.execute(
            select(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(10)
        )
        
        conversations = result.scalars().all()
        print(f"Found {len(conversations)} conversations")
        
        for conv in conversations:
            print(f"  - {conv.id}: {conv.title}")

# Run it
asyncio.run(get_recent_conversations())
```

---

## Configuration

### Environment Variables

The SDK uses Pydantic BaseSettings for configuration:

```bash
# Database
export BRAINCELL_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/braincell_dev"

# Weaviate (semantic search)
export BRAINCELL_WEAVIATE_URL="http://localhost:8080"

# Redis (caching)
export BRAINCELL_REDIS_URL="redis://localhost:6379"

# Logging
export BRAINCELL_LOG_LEVEL="DEBUG"

# API
export BRAINCELL_API_HOST="0.0.0.0"
export BRAINCELL_API_PORT=9504
```

### Load Settings in Code

```python
from itl_braincell_sdk.core import get_settings

settings = get_settings()
print(f"Database: {settings.database_url}")
print(f"Weaviate: {settings.weaviate_url}")
print(f"Log Level: {settings.log_level}")
```

---

## Running Tests

### Prerequisites

```bash
pip install pytest pytest-asyncio pytest-cov
```

### Run SDK Tests

```bash
cd /path/to/ITL.Braincell.SDK

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/cells/test_conversations.py -v

# Run with debug output
pytest -v -s
```

### Test Configuration

Create `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Common Test Pattern

```python
import pytest
from itl_braincell_sdk.core import AsyncSessionLocal
from itl_braincell_sdk.cells.conversations.model import Conversation

@pytest.fixture
async def db_session():
    """Fixture providing a test database session."""
    async with AsyncSessionLocal() as session:
        yield session
        # Auto-cleanup after test

@pytest.mark.asyncio
async def test_create_conversation(db_session):
    # Create a test conversation
    conversation = Conversation(
        title="Test Conversation",
        content="Hello, world!"
    )
    db_session.add(conversation)
    await db_session.commit()
    
    # Verify it was created
    assert conversation.id is not None
    assert conversation.title == "Test Conversation"
```

---

## Third Example: Use in FastAPI

Integrate BrainCell into a FastAPI application:

```python
from fastapi import FastAPI, Depends
from sqlalchemy import select
from itl_braincell_sdk.core import AsyncSessionLocal, get_async_db
from itl_braincell_sdk.cells import discover_cells
from itl_braincell_sdk.cells.conversations.model import Conversation
from itl_braincell_sdk.cells.conversations.schema import ConversationCreate

app = FastAPI(title="My Memory API")

# Dependency for database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Endpoint: List conversations
@app.get("/conversations")
async def list_conversations(
    db = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    result = await db.execute(
        select(Conversation)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    conversations = result.scalars().all()
    return conversations

# Endpoint: Create conversation
@app.post("/conversations")
async def create_conversation(
    conv: ConversationCreate,
    db = Depends(get_db)
):
    new_conv = Conversation(**conv.model_dump())
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)
    return new_conv

# Startup: Initialize database and discover cells
@app.on_event("startup")
async def startup():
    # Discover all cells
    cells = discover_cells()
    print(f"✓ Loaded {len(cells)} cells")
    
    # Import models (registers with Base.metadata)
    for cell in cells:
        cell.get_models()
    
    print("✓ Database models registered")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run it:

```bash
pip install fastapi uvicorn
python app.py

# Test it
curl http://localhost:8000/conversations
```

---

## Fourth Example: Create Your First Cell

Create a simple custom cell:

```python
# my_cell/cell.py
from itl_braincell_sdk.cells import MemoryCell
from fastapi import APIRouter

class MyCustomCell(MemoryCell):
    @property
    def name(self) -> str:
        return "my_custom"
    
    @property
    def prefix(self) -> str:
        return "/api/my-custom"
    
    def get_router(self) -> APIRouter:
        router = APIRouter()
        
        @router.get("")
        async def list_items():
            return {"items": [], "count": 0}
        
        @router.post("")
        async def create_item(name: str, value: str):
            return {"id": 1, "name": name, "value": value}
        
        return router
    
    def get_models(self):
        # No models for this simple example
        pass
    
    def register_mcp_tools(self, mcp):
        # Register a tool for Claude
        @mcp.tool()
        async def list_my_items() -> str:
            """List all items in my custom cell."""
            return "Here are the items"

# Create instance
cell = MyCustomCell()
```

Use it in your app:

```python
from fastapi import FastAPI
from my_cell.cell import cell

app = FastAPI()

# Mount the cell's router
app.include_router(cell.get_router(), prefix=cell.prefix)

# Run: GET http://localhost:8000/api/my-custom
```

---

## What's Next?

### Learn More About

- **Cells** → [Architecture Overview](00-OVERVIEW.md#memory-cell)
- **Plugins** → [Architecture Overview](00-OVERVIEW.md#plugin) and [Plugin Development Guide](03-PLUGIN-DEVELOPMENT.md)
- **Database** → [Deployment Guide](05-DEPLOYMENT.md)
- **Configuration** → [Deployment Guide](05-DEPLOYMENT.md#configuration)

### Build Something

- Create a custom cell (see example above)
- Create a plugin package
- Integrate BrainCell into your FastAPI app
- Deploy to Docker

### Common Next Steps

1. **Read the Architecture** — [00-OVERVIEW.md](00-OVERVIEW.md)
2. **Build a Plugin** — [03-PLUGIN-DEVELOPMENT.md](03-PLUGIN-DEVELOPMENT.md)
3. **Check Examples** — [07-EXAMPLES/](07-EXAMPLES/)
4. **Deploy** — [05-DEPLOYMENT.md](05-DEPLOYMENT.md)

---

## Troubleshooting

### ImportError: No module named 'itl_braincell_sdk'

**Solution:**
```bash
# Install in development mode
pip install -e .

# Or install from PyPI
pip install itl-braincell-sdk
```

### Database Connection Error

**Solution:**
```bash
# Check database is running
psql -U postgres -d braincell_dev -c "SELECT 1"

# Check environment variable
echo $BRAINCELL_DATABASE_URL

# Test connection
python -c "from itl_braincell_sdk.core import get_async_db; print('✓ Connected')"
```

### Cell Not Discovered

**Solution:**
```python
# Verify cell is discoverable
from itl_braincell_sdk.cells import discover_cells
cells = discover_cells()
print([c.name for c in cells])

# Check cell exports
from my_package.cells import cell  # Should work
```

### Migration Fails

**Solution:**
```bash
# Check migration history
python -m alembic current
python -m alembic history

# Stamp without running (if already applied)
python -m alembic stamp head
```

---

## Complete Working Example

Create `example.py`:

```python
"""Complete example: Create, migrate, and query a database."""
import asyncio
from sqlalchemy import select
from itl_braincell_sdk.core import (
    get_settings,
    AsyncSessionLocal,
    init_db,
    Base
)
from itl_braincell_sdk.cells import discover_cells

async def main():
    # 1. Load settings
    settings = get_settings()
    print(f"✓ Settings loaded")
    print(f"  Database: {settings.database_url}")
    
    # 2. Discover cells
    cells = discover_cells()
    print(f"✓ Discovered {len(cells)} cells")
    
    # 3. Import models
    for cell in cells:
        cell.get_models()
    print(f"✓ Models imported and registered")
    
    # 4. Initialize database
    await init_db()
    print(f"✓ Database initialized")
    
    # 5. Query database
    async with AsyncSessionLocal() as session:
        # Example: Count notes
        result = await session.execute(
            select(lambda: "SELECT COUNT(*) FROM notes")
        )
        count = result.scalar()
        print(f"✓ Found {count} notes in database")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
export BRAINCELL_DATABASE_URL="postgresql+asyncpg://postgres:password@localhost/braincell_dev"
python example.py
```

Expected output:

```
✓ Settings loaded
  Database: postgresql+asyncpg://postgres:password@localhost/braincell_dev
✓ Discovered 4 cells
✓ Models imported and registered
✓ Database initialized
✓ Found 0 notes in database
```

---

## Summary

✅ Installed BrainCell SDK  
✅ Set up database  
✅ Discovered cells  
✅ Queried data  
✅ Created custom cell  
✅ Integrated with FastAPI  

**Next:** [Architecture Overview](00-OVERVIEW.md) or [Plugin Development](03-PLUGIN-DEVELOPMENT.md)
