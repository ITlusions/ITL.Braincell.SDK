# Code Examples

Practical code examples for common BrainCell SDK tasks.

## Table of Examples

1. [Quick Start](#quick-start) — Hello World
2. [Cell Operations](#cell-operations) — CRUD operations
3. [Plugin Development](#plugin-development) — Build a plugin
4. [Async Patterns](#async-patterns) — Working with async
5. [FastAPI Integration](#fastapi-integration) — Integrate with FastAPI
6. [Testing](#testing) — Write tests

---

## Quick Start

### Example 1: Discover and List Cells

**File: `01_discover_cells.py`**

```python
\"\"\"Discover all available memory cells.\"\"\"
from itl_braincell_sdk.cells import discover_cells

# Discover cells from SDK only
print("SDK Cells:")
cells = discover_cells()
for cell in cells:
    print(f\"  - {cell.name} ({cell.prefix})\")

# Discover cells from SDK + plugins
print(\"\\nAll Cells (including plugins):\")
cells = discover_cells(include_plugins=True)
for cell in cells:
    print(f\"  - {cell.name}\")

print(f\"\\nTotal: {len(cells)} cells\")
```

**Run:**
```bash
python 01_discover_cells.py

# Output:
# SDK Cells:
#   - conversations (/api/conversations)
#   - notes (/api/notes)
#   - snippets (/api/snippets)
#   - files_discussed (/api/files_discussed)
#
# All Cells (including plugins):
#   - conversations
#   - notes
#   - snippets
#   - files_discussed
#
# Total: 4 cells
```

---

## Cell Operations

### Example 2: Query Database

**File: `02_query_database.py`**

```python
\"\"\"Query memory cells using SQLAlchemy.\"\"\"
import asyncio
from sqlalchemy import select
from itl_braincell_sdk.core import AsyncSessionLocal
from itl_braincell_sdk.cells.conversations.model import Conversation

async def list_conversations():
    \"\"\"Get all conversations from database.\"\"\"
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Conversation))
        conversations = result.scalars().all()
        
        print(f\"Found {len(conversations)} conversations:\")
        for conv in conversations:
            print(f\"  - {conv.id}: {conv.title}\")
        
        return conversations

async def create_conversation(title: str, content: str):
    \"\"\"Create a new conversation.\"\"\"
    async with AsyncSessionLocal() as session:
        conversation = Conversation(
            title=title,
            content=content
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        
        print(f\"Created conversation: {conversation.id}\")
        return conversation

async def main():
    # List existing
    await list_conversations()
    
    # Create new
    await create_conversation(
        title=\"Test Conversation\",
        content=\"This is a test\"
    )
    
    # List updated
    await list_conversations()

# Run it
asyncio.run(main())
```

**Run:**
```bash
export BRAINCELL_DATABASE_URL=\"postgresql+asyncpg://postgres:password@localhost/braincell\"
python 02_query_database.py
```

---

### Example 3: Custom CRUD Cell

**File: `03_custom_cell.py`**

```python
\"\"\"Create and use a custom memory cell.\"\"\"
from fastapi import APIRouter, HTTPException
from sqlalchemy import Column, Integer, String, DateTime, select
from datetime import datetime
from itl_braincell_sdk.cells import MemoryCell
from itl_braincell_sdk.core import AsyncSessionLocal, Base
from pydantic import BaseModel

# ============= Model =============
class Article(Base):
    __tablename__ = \"articles\"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String(5000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============= Schema =============
class ArticleCreate(BaseModel):
    title: str
    content: str

class ArticleRead(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= Cell =============
class ArticleCell(MemoryCell):
    \"\"\"Memory cell for storing articles.\"\"\"
    
    @property
    def name(self) -> str:
        return \"articles\"
    
    @property
    def prefix(self) -> str:
        return \"/api/articles\"
    
    def get_router(self) -> APIRouter:
        router = APIRouter()
        
        @router.get(\"\", response_model=list[ArticleRead])
        async def list_articles():
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Article))
                return result.scalars().all()
        
        @router.post(\"\", response_model=ArticleRead)
        async def create_article(article: ArticleCreate):
            async with AsyncSessionLocal() as session:
                db_article = Article(**article.model_dump())
                session.add(db_article)
                await session.commit()
                await session.refresh(db_article)
                return db_article
        
        @router.get(\"/{article_id}\", response_model=ArticleRead)
        async def get_article(article_id: int):
            async with AsyncSessionLocal() as session:
                article = await session.get(Article, article_id)
                if not article:
                    raise HTTPException(status_code=404)
                return article
        
        return router
    
    def get_models(self):
        pass  # Already imported above
    
    def register_mcp_tools(self, mcp):
        @mcp.tool()
        async def list_articles_tool() -> str:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Article))
                articles = result.scalars().all()
                return f\"Found {len(articles)} articles\"

# ============= Usage =============
if __name__ == \"__main__\":
    cell = ArticleCell()
    print(f\"Cell created: {cell.name}\")
    print(f\"API prefix: {cell.prefix}\")
    
    # In FastAPI:
    # app.include_router(cell.get_router(), prefix=cell.prefix)
```

---

## Plugin Development

### Example 4: Simple Plugin

**File: `04_simple_plugin.py`**

```python
\"\"\"Create a simple plugin.\"\"\"
from pydantic_settings import BaseSettings
from itl_braincell_sdk.plugins import CellCollectionPlugin, PluginMetadata
from itl_braincell_sdk.cells import MemoryCell
from fastapi import APIRouter

# ============= Configuration =============
class MyPluginConfig(BaseSettings):
    api_url: str = \"https://api.example.com\"
    api_key: str = \"\"
    
    class Config:
        env_prefix = \"BRAINCELL_MYPLUGIN_\"

# ============= Simple Cell =============
class SimpleCell(MemoryCell):
    @property
    def name(self) -> str:
        return \"simple\"
    
    @property
    def prefix(self) -> str:
        return \"/api/simple\"
    
    def get_router(self) -> APIRouter:
        router = APIRouter()
        
        @router.get(\"\")
        async def hello():
            return {\"message\": \"Hello from Simple Cell\"}
        
        return router
    
    def get_models(self):
        pass
    
    def register_mcp_tools(self, mcp):
        @mcp.tool()
        async def hello_tool() -> str:
            return \"Hello from MCP!\"

# ============= Plugin =============
class MyPlugin(CellCollectionPlugin):
    @property
    def name(self) -> str:
        return \"myplugin\"
    
    @property
    def description(self) -> str:
        return \"My simple plugin\"
    
    @property
    def config_class(self):
        return MyPluginConfig
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=\"myplugin\",
            version=\"0.1.0\",
            api_version=\"1.0\"
        )
    
    def get_cells(self):
        return [SimpleCell()]
    
    async def on_install(self):
        config = self.get_config()\n        print(f\"Initialized MyPlugin with API: {config.api_url}\")
    
    async def on_uninstall(self):
        print(\"Cleaning up MyPlugin\")
    
    async def health_check(self) -> bool:
        config = self.get_config()
        if not config.api_key:
            print(\"Warning: API key not set\")
            return False
        return True
    
    async def get_metrics(self) -> dict:
        return {\"status\": \"healthy\"}

# ============= Usage =============
if __name__ == \"__main__\":
    plugin = MyPlugin()
    print(f\"Plugin: {plugin.name}\")
    print(f\"Cells: {[c.name for c in plugin.get_cells()]}\")
    print(f\"Metadata: {plugin.metadata}\")
```

---

## Async Patterns

### Example 5: Common Async Patterns

**File: `05_async_patterns.py`**

```python
\"\"\"Common async patterns in BrainCell.\"\"\"
import asyncio
from sqlalchemy import select
from itl_braincell_sdk.core import AsyncSessionLocal
from itl_braincell_sdk.cells.conversations.model import Conversation

# ============= Pattern 1: Simple Query =============
async def pattern_simple_query():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Conversation))
        conversations = result.scalars().all()
        return conversations

# ============= Pattern 2: Create and Return =============
async def pattern_create_and_return(title: str):
    async with AsyncSessionLocal() as session:
        conv = Conversation(title=title, content=\"Test\")
        session.add(conv)
        await session.commit()
        await session.refresh(conv)
        return conv

# ============= Pattern 3: Concurrent Operations =============
async def pattern_concurrent():
    # Run multiple operations at the same time
    tasks = [
        pattern_simple_query(),
        pattern_simple_query(),
        pattern_simple_query(),
    ]
    results = await asyncio.gather(*tasks)
    return results

# ============= Pattern 4: Error Handling =============
async def pattern_error_handling():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Conversation))
            return result.scalars().all()
    except Exception as e:
        print(f\"Error: {e}\")
        return []

# ============= Pattern 5: Transaction =============
async def pattern_transaction():
    async with AsyncSessionLocal() as session:
        try:
            # Multiple operations in one transaction
            conv1 = Conversation(title=\"A\", content=\"Test A\")
            conv2 = Conversation(title=\"B\", content=\"Test B\")
            
            session.add(conv1)
            session.add(conv2)
            
            # If any fails, both rollback
            await session.commit()
            
            return [conv1, conv2]
        except Exception as e:
            await session.rollback()
            print(f\"Transaction failed: {e}\")
            return []

# ============= Run All =============
async def main():
    print(\"Pattern 1: Simple Query\")
    result = await pattern_simple_query()
    print(f\"  Found {len(result)} conversations\\n\")
    
    print(\"Pattern 2: Create and Return\")
    result = await pattern_create_and_return(\"Example\")
    print(f\"  Created: {result.title}\\n\")
    
    print(\"Pattern 3: Concurrent Operations\")
    results = await pattern_concurrent()
    print(f\"  Ran {len(results)} queries concurrently\\n\")
    
    print(\"Pattern 4: Error Handling\")
    result = await pattern_error_handling()
    print(f\"  Got {len(result)} results\\n\")
    
    print(\"Pattern 5: Transaction\")
    result = await pattern_transaction()
    print(f\"  Created {len(result)} items\\n\")

asyncio.run(main())
```

---

## FastAPI Integration

### Example 6: Full FastAPI App

**File: `06_fastapi_app.py`**

```python
\"\"\"Complete FastAPI application with BrainCell.\"\"\"
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from itl_braincell_sdk.cells import discover_cells, discover_cell_plugins
from itl_braincell_sdk.core import get_async_db

# ============= Lifespan =============
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(\"Starting BrainCell API...\")
    
    # Discover and mount cells
    cells = discover_cells(include_plugins=True)
    for cell in cells:
        router = cell.get_router()
        app.include_router(router, prefix=cell.prefix, tags=[cell.name])
        print(f\"  ✓ Mounted {cell.name}\")
    
    # Discover and initialize plugins
    plugins = discover_cell_plugins()
    for plugin in plugins:
        try:
            await plugin.on_install()
            print(f\"  ✓ Initialized {plugin.name}\")
        except Exception as e:
            print(f\"  ✗ Failed to initialize {plugin.name}: {e}\")
    
    yield
    
    # Shutdown
    print(\"Shutting down...\")
    for plugin in plugins:
        try:
            await plugin.on_uninstall()
            print(f\"  ✓ Cleaned up {plugin.name}\")
        except Exception as e:
            print(f\"  ✗ Failed to clean up {plugin.name}: {e}\")

# ============= Application =============
app = FastAPI(
    title=\"BrainCell API\",
    version=\"0.1.0\",
    lifespan=lifespan
)

# ============= Routes =============
@app.get(\"/health\")
async def health():
    return {\"status\": \"healthy\"}

@app.get(\"/\")
async def root():
    return {\n        \"message\": \"BrainCell API\",\n        \"docs\": \"/docs\",\n        \"redoc\": \"/redoc\"\n    }

# ============= Run =============
if __name__ == \"__main__\":
    import uvicorn
    uvicorn.run(app, host=\"0.0.0.0\", port=9504)
```

**Run:**
```bash
python 06_fastapi_app.py
# Visit: http://localhost:9504/docs
```

---

## Testing

### Example 7: Unit Tests

**File: `07_tests.py`**

```python
\"\"\"Test examples using pytest.\"\"\"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from itl_braincell_sdk.core import AsyncSessionLocal
from itl_braincell_sdk.cells.conversations.model import Conversation

# ============= Fixtures =============
@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session

@pytest.fixture
def api_client():
    from main import app
    return TestClient(app)

# ============= Unit Tests =============
@pytest.mark.asyncio
async def test_create_conversation(db_session):
    \"\"\"Test creating a conversation.\"\"\"
    conv = Conversation(
        title=\"Test\",
        content=\"Test content\"
    )
    db_session.add(conv)
    await db_session.commit()
    
    assert conv.id is not None
    assert conv.title == \"Test\"

@pytest.mark.asyncio
async def test_query_conversations(db_session):
    \"\"\"Test querying conversations.\"\"\"
    # Create test data
    conv = Conversation(title=\"Test\", content=\"Test\")
    db_session.add(conv)
    await db_session.commit()
    
    # Query
    result = await db_session.execute(select(Conversation))
    conversations = result.scalars().all()
    
    assert len(conversations) > 0
    assert conversations[0].title == \"Test\"

# ============= API Tests =============
def test_api_health(api_client):
    \"\"\"Test API health endpoint.\"\"\"
    response = api_client.get(\"/health\")
    assert response.status_code == 200
    assert response.json()[\"status\"] == \"healthy\"

def test_api_conversations(api_client):
    \"\"\"Test conversations API.\"\"\"
    response = api_client.get(\"/api/conversations\")
    assert response.status_code in [200, 404]  # 200 or 404 depending on routes

# ============= Run Tests =============
# pytest 07_tests.py -v
```

---

## Summary

| Example | Topic | File |
|---------|-------|------|
| 1 | Discover cells | `01_discover_cells.py` |
| 2 | Query database | `02_query_database.py` |
| 3 | Custom cell | `03_custom_cell.py` |
| 4 | Simple plugin | `04_simple_plugin.py` |
| 5 | Async patterns | `05_async_patterns.py` |
| 6 | FastAPI app | `06_fastapi_app.py` |
| 7 | Testing | `07_tests.py` |

**Next:** [Architecture](02-ARCHITECTURE.md) or [Deployment](05-DEPLOYMENT.md)
