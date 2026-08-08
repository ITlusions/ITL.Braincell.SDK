# BrainCell SDK Documentation

Complete technical documentation for the ITL BrainCell SDK — the core library powering the persistent memory platform.

## 📚 Documentation Structure

Start with your use case:

### **For Users & Developers**
- **[Getting Started](01-GETTING-STARTED.md)** — Install, set up, and run your first example
- **[Architecture Overview](00-OVERVIEW.md)** — Understand cells, plugins, and the system design
- **[API Reference](04-API-REFERENCE.md)** — Complete SDK API documentation
- **[Knowledge Systems & RAG](08-AI-KNOWLEDGE-SYSTEMS.md)** — Vector search, semantic queries, AI integration
- **[RAG Explained](09-RAG-EXPLAINED.md)** — Learn about Retrieval-Augmented Generation (upcoming feature)

### **For Plugin Developers**
- **[Plugin Development Guide](03-PLUGIN-DEVELOPMENT.md)** — Create your first plugin
- **[Examples](07-EXAMPLES/)** — Real-world plugin examples
- **[Advanced Features](02-ARCHITECTURE.md#advanced-plugin-features)** — Configuration, lifecycle hooks, dependencies, bundling, hot reload

### **For Platform Integration**
- **[Amalia Integration Guide](10-AMALIA-INTEGRATION.md)** — Integrate Amalia threat detection with BrainCell persistence
  - 3-phase roadmap: Synchronous API (Sprint 3) → Async queue (Sprint 4) → MCP tools (Sprint 5)
  - Finding storage mapping (where each threat type gets stored)
  - Implementation guide with code examples
  - Quick wins and deployment procedures

### **For DevOps & Operations**
- **[Deployment Guide](05-DEPLOYMENT.md)** — Docker, migrations, production setup
- **[Troubleshooting](06-TROUBLESHOOTING.md)** — Common issues and solutions

### **For Maintainers**
- **[Architecture Deep Dive](02-ARCHITECTURE.md)** — System design, folder structure, extension points
- **[CI/CD Pipeline](../PIPELINE.md)** — Build, test, release workflows

---

## 🚀 Quick Start

### Installation
```bash
# Local development
pip install -e .

# From another project
pip install itl-braincell-sdk
```

### First Example
```python
from itl_braincell_sdk.cells import discover_cells
from itl_braincell_sdk.core import get_async_db

# Discover all available cells
cells = discover_cells()
print([cell.name for cell in cells])

# Use database
async with get_async_db() as db:
    # Query memory cells
    pass
```

See [Getting Started](01-GETTING-STARTED.md) for more.

---

## 📖 What Is BrainCell?

**BrainCell** is a persistent memory platform that organizes information into specialized **memory cells** — each focused on a specific domain (conversations, threats, code decisions, etc).

**Key Concepts:**
- **Memory Cell** — Self-contained domain for storing and retrieving information
- **Plugin** — Collection of cells that work together (e.g., "security-ops" plugin)
- **SDK** — This package; provides core infrastructure, base cells, and plugin system

**Example Cells:**
- `conversations` — Chat history and context
- `notes` — General observations
- `snippets` — Code and documentation snippets
- `threats` → `security` plugin — Security threats and incidents
- `architecture_notes` → `architecture` plugin — Design decisions

All cells use the same database, can cross-reference each other, and benefit from unified infrastructure.

---

## 🏗️ System Architecture

```
BrainCell SDK (this package)
├── Core Infrastructure
│   ├── Database (async SQLAlchemy + PostgreSQL)
│   ├── Vector Search (Weaviate integration)
│   ├── ORM Models (Base, mixins, common fields)
│   └── Pydantic Schemas (request/response validation)
├── Memory Cells (4 core cells in SDK)
│   ├── conversations/
│   ├── notes/
│   ├── snippets/
│   └── files_discussed/
├── Plugin System
│   ├── CellCollectionPlugin ABC
│   ├── Auto-discovery via entry points
│   ├── Dependency validation
│   ├── Lifecycle hooks (init/cleanup)
│   ├── Configuration management
│   └── Hot reload system
└── Services
    ├── Weaviate integration
    ├── Data synchronization
    └── Retention policies
```

---

## 📦 Packages & Repos

| Package | Purpose | Language | Link |
|---------|---------|----------|------|
| **ITL.Braincell.SDK** | Core library (this) | Python | [Repo](https://github.com/ITlusions/ITL.Braincell.SDK) |
| **ITL.BrainCell.Api** | REST API | Python | [Repo](https://github.com/ITlusions/ITL.BrainCell.Api) |
| **ITL.BrainCell.Mcp** | MCP server | Python | [Repo](https://github.com/ITlusions/ITL.BrainCell.Mcp) |
| **ITL.BrainCell.Dashboard** | Web UI | Python | [Repo](https://github.com/ITlusions/ITL.BrainCell.Dashboard) |
| **ITL.Braincell.Cells*** | Plugin packages | Python | [Org](https://github.com/ITlusions) |

*Security, Architecture, Codebase, Operations, and more

---

## 🔗 Document Map

```
docs/
├── README.md (you are here)
├── 00-OVERVIEW.md
│   ├── What is a memory cell?
│   ├── What is a plugin?
│   ├── SDK folder structure
│   ├── Core infrastructure
│   └── Memory cell contract
├── 01-GETTING-STARTED.md
│   ├── Installation
│   ├── First example
│   ├── Database setup
│   ├── Running tests
│   └── Common next steps
├── 02-ARCHITECTURE.md
│   ├── System design
│   ├── Cell discovery mechanism
│   ├── Plugin discovery mechanism
│   ├── Automatic model discovery (migrations)
│   ├── Advanced plugin features
│   └── Extension points
├── 03-PLUGIN-DEVELOPMENT.md
│   ├── Plugin anatomy
│   ├── Step-by-step guide
│   ├── Project structure
│   ├── Testing plugins
│   └── Publishing plugins
├── 04-API-REFERENCE.md
│   ├── Core API
│   ├── Cell API
│   ├── Plugin API
│   ├── Database API
│   └── Service API
├── 05-DEPLOYMENT.md
│   ├── Docker setup
│   ├── Database migrations
│   ├── Configuration
│   ├── Production checklist
│   └── Troubleshooting deployment
├── 06-TROUBLESHOOTING.md
│   ├── Common issues
│   ├── Debug logging
│   ├── Database errors
│   ├── Plugin errors
│   └── Performance tuning
└── 07-EXAMPLES/
    ├── 01-hello-world-cell.py
    ├── 02-plugin-with-config.py
    ├── 03-async-service.py
    ├── 04-lifecycle-hooks.py
    └── README.md (guide)└── 08-AI-KNOWLEDGE-SYSTEMS.md
    ├── RAG (Retrieval-Augmented Generation)
    ├── KMS features overview
    ├── Semantic search techniques
    ├── Knowledge graphs
    ├── Implementation roadmap
    └── Architecture patterns
└── 09-RAG-EXPLAINED.md
    ├── RAG concept explained simply
    ├── Step-by-step how it works
    ├── Real examples for BrainCell
    ├── Current vs future capabilities
    ├── Phase-by-phase implementation
    └── Technical architecture```

---

## 🎯 Documentation By Role

### **I'm a User**
Starting point: [01-GETTING-STARTED.md](01-GETTING-STARTED.md)
- Install the SDK
- Understand the database
- Query memory cells
- Next: Import into your project

### **I'm Building a Plugin**
Starting point: [03-PLUGIN-DEVELOPMENT.md](03-PLUGIN-DEVELOPMENT.md)
- Learn plugin structure
- Create first plugin
- Add configuration, lifecycle hooks
- Test and publish
- Advanced: [02-ARCHITECTURE.md](02-ARCHITECTURE.md#advanced-plugin-features)

### **I'm Deploying BrainCell**
Starting point: [05-DEPLOYMENT.md](05-DEPLOYMENT.md)
- Docker setup
- Environment configuration
- Run migrations
- Verify it works
- Troubleshooting: [06-TROUBLESHOOTING.md](06-TROUBLESHOOTING.md)

### **I'm Contributing/Maintaining**
Starting point: [02-ARCHITECTURE.md](02-ARCHITECTURE.md)
- System design
- Cell structure
- Plugin system internals
- Extension points
- CI/CD: [../PIPELINE.md](../PIPELINE.md)

### **I'm Planning Future Features**
Starting point: [08-AI-KNOWLEDGE-SYSTEMS.md](08-AI-KNOWLEDGE-SYSTEMS.md)
- RAG (Retrieval-Augmented Generation) patterns
- Knowledge Management System features
- Semantic search implementation
- Knowledge graph architecture
- Entity extraction and linking
- Implementation roadmap

**For detailed RAG explanation:** See [09-RAG-EXPLAINED.md](09-RAG-EXPLAINED.md)

---

## 🔑 Key Features

✅ **Automatic Model Discovery**
- Models auto-discovered at migration and startup time
- No hardcoded imports needed
- Scales to unlimited cells and plugins

✅ **Plugin System**
- Install plugins via pip, auto-discovered via entry points
- Configuration management (environment variables)
- Lifecycle hooks (init, cleanup, health checks)
- Dependency validation
- Plugin bundling
- Hot reload capability

✅ **Async-First Architecture**
- Built on async/await (Python 3.12+)
- SQLAlchemy 2.0 async support
- Non-blocking database operations
- Ready for FastAPI/Starlette

🔧 **Smart Search & Retrieval** (Planned Roadmap)
- Semantic search across all cell types
- Hybrid search combining semantic + keyword matching
- Intelligent result reranking for relevance
- Built on Weaviate vector database
- Powers RAG (Retrieval-Augmented Generation)
- See [AI Knowledge Systems](08-AI-KNOWLEDGE-SYSTEMS.md) for implementation roadmap

✅ **Production Ready**
- Comprehensive error handling
- Structured logging
- Health checks
- Metrics collection
- Database migrations (Alembic)
- Type hints throughout

✅ **Extensible**
- Cell plugin system
- Custom services
- Weaviate integration for semantic search
- Multiple deployment options

---

## 🚦 Status

| Component | Status | Version |
|-----------|--------|---------|
| Core SDK | ✅ Stable | 0.1.0+ |
| Plugin System | ✅ Stable | Latest |
| Automatic Discovery | ✅ Stable | Latest |
| Hot Reload | ✅ Stable | Latest |
| Semantic Search | 🔧 Planned | Roadmap |
| Hybrid Search | 🔧 Planned | Roadmap |
| Intelligent Reranking | 🔧 Planned | Roadmap |
| CLI Tools | 🔧 In Progress | - |
| GraphQL API | 🔧 Planned | - |
| Marketplace | 🔧 Planned | - |

---

## 📞 Getting Help

- **Questions?** Start with [Troubleshooting](06-TROUBLESHOOTING.md)
- **Examples?** Check [Examples](07-EXAMPLES/)
- **Bug reports?** Open an issue on GitHub
- **Contributions?** See [Contributing](../CONTRIBUTING.md)

---

## 📝 Document Versions

| Document | Last Updated | Status |
|----------|--------------|--------|
| [00-OVERVIEW.md](00-OVERVIEW.md) | 2026-08-03 | Current |
| [01-GETTING-STARTED.md](01-GETTING-STARTED.md) | 2026-08-03 | Current |
| [02-ARCHITECTURE.md](02-ARCHITECTURE.md) | 2026-08-03 | Current |
| [03-PLUGIN-DEVELOPMENT.md](03-PLUGIN-DEVELOPMENT.md) | 2026-08-03 | Current |
| [04-API-REFERENCE.md](04-API-REFERENCE.md) | 2026-08-03 | Current |
| [05-DEPLOYMENT.md](05-DEPLOYMENT.md) | 2026-08-03 | Current |
| [06-TROUBLESHOOTING.md](06-TROUBLESHOOTING.md) | 2026-08-03 | Current |

---

## 📄 Table of Contents (All Docs)

1. **[Overview](00-OVERVIEW.md)** — What is the SDK? Architecture overview.
2. **[Getting Started](01-GETTING-STARTED.md)** — Installation, first example, testing.
3. **[Architecture](02-ARCHITECTURE.md)** — Deep dive into design, cells, plugins.
4. **[Plugin Development](03-PLUGIN-DEVELOPMENT.md)** — Build your first plugin.
5. **[API Reference](04-API-REFERENCE.md)** — Complete SDK API docs.
6. **[Deployment](05-DEPLOYMENT.md)** — Docker, migrations, production setup.
7. **[Troubleshooting](06-TROUBLESHOOTING.md)** — Common issues & solutions.
8. **[Examples](07-EXAMPLES/)** — Code examples.

---

**Next:** Start with [Getting Started](01-GETTING-STARTED.md) or [Overview](00-OVERVIEW.md)
