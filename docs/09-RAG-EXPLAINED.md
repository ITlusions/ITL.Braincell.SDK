# RAG (Retrieval-Augmented Generation) Explained

**Status:** 🔧 Planned for Phase 1-3 implementation (see [08-AI-KNOWLEDGE-SYSTEMS.md](08-AI-KNOWLEDGE-SYSTEMS.md))

## The Problem RAG Solves

Imagine you ask BrainCell: **"What security threats relate to the authentication system we discussed?"**

Without RAG, a traditional system would either:
- ❌ Not find the connection (keyword search fails)
- ❌ Return irrelevant results (matches "security" + "system" but misses context)
- ❌ Rely on hardcoded links (doesn't scale)

## How RAG Works (Step-by-Step)

### **Step 1: Convert to Meaning (Vector Embeddings)**

```
Text: "We discovered a SQL injection vulnerability in the login form"
      ↓
Vector: [0.23, -0.15, 0.89, 0.12, ..., 0.45]  ← numerical representation of meaning
```

The vector captures **semantic meaning**, not just words. Similar concepts get similar vectors:
- "SQL injection" ≈ "database attack" ≈ "code injection" (close vectors)
- "database" ≠ "sandwich" (far apart vectors)

**BrainCell already has this:** Weaviate stores vectors for conversations, threats, etc.

---

### **Step 2: Store in Vector Database**

```
Weaviate (Vector DB in BrainCell)
├── Conversation #1: "Discussed authentication design"
│   └── Vector: [0.23, -0.15, 0.89, ...]
├── Threat #5: "SQL injection in login form"
│   └── Vector: [0.24, -0.14, 0.88, ...]  ← Similar to Conversation #1
└── Code snippet #12: "Hash password function"
    └── Vector: [0.25, -0.13, 0.87, ...]
```

---

### **Step 3: Retrieve Relevant Documents (Before Answering)**

User query: **"What security threats relate to authentication?"**

Convert query to vector → Find all similar vectors in Weaviate → **Rank by relevance**

```
Query vector: [0.22, -0.16, 0.90, ...]
         ↓
         Matches in Weaviate:
         1. Threat #5 (SQL injection) - 95% match
         2. Conversation #1 (auth design) - 92% match
         3. Code snippet #12 (hash function) - 88% match
         4. Note #8 (password policy) - 85% match
```

---

### **Step 4: Hybrid Search (Semantic + Keyword)**

RAG combines two search methods:

```
Query: "What security threats relate to authentication?"

A) SEMANTIC SEARCH (Vector-based)
   └─ Finds: SQL injection, password attacks, session hijacking
      (Things that MEAN related things)

B) FULL-TEXT SEARCH (Keyword-based)
   └─ Finds: Anything with words "security" + "authentication"
      (Literal phrase matches)

C) HYBRID (Best of both)
   └─ Returns results that are BOTH semantically similar 
      AND keyword-relevant
      (Most accurate)
```

**Why both?** 
- Semantic alone: Might miss specific threat names ("SQL injection" vs "database attack")
- Keyword alone: Might return false positives ("securing authentication" ≠ "security threat")
- Hybrid: Gets the best of both worlds

---

### **Step 5: Rerank Results**

Sometimes relevance isn't obvious. RAG can rerank based on:

```
Initial Ranking:        →    Reranked Results:
1. Threat #5 (95%)            1. Threat #5 - SQL injection
2. Conversation #1 (92%)         (Directly answers query)
3. Code snippet (88%)      →  2. Conversation #1 - Auth design
4. Note #8 (85%)              (Context for why threat matters)
                           3. Code snippet - Hash function
                              (How to fix it)
                           4. Note #8 - Policy
                              (Compliance requirement)
```

---

## Real Example for BrainCell

### **Without RAG:**
```
User: "Why did we choose JWT over sessions?"
System: Shows only notes tagged with "JWT" or "sessions"
❌ Misses related threats, code decisions, conversations
```

### **With RAG:**
```
User: "Why did we choose JWT over sessions?"
System: 
  1. Retrieves Conversation #3: "Discussed JWT vs sessions"
  2. Retrieves Decision #7: "Chose JWT for microservices"
  3. Retrieves Threat #12: "Session fixation vulnerability"
  4. Retrieves Code #45: "JWT implementation in auth.py"
  5. Retrieves Note #8: "JWT token expiration policy"

✅ Context-aware, comprehensive answer
```

---

## Key Features Breakdown

| Feature | What It Does | Example |
|---------|-------------|---------|
| **Vector Embeddings** | Converts text to meaning | "SQL injection" → mathematical vector |
| **Vector Database (Weaviate)** | Stores all vectors efficiently | Finds similar items in milliseconds |
| **Semantic Retrieval** | Finds conceptually related items | "database attack" finds "SQL injection" |
| **Full-Text Search** | Finds keyword matches | Looks for exact words in text |
| **Hybrid Search** | Combines both | Most accurate results |
| **Reranking** | Sorts by importance | Puts most relevant results first |

---

## How BrainCell Will Use RAG

### **Current State (0.1.0+):**
- ✅ Weaviate (vector storage) — already in place
- ✅ Cells (organized data) — already organized
- ❌ Semantic connection between cells — not automated
- ❌ Context-aware search — not smart

### **With RAG Enhancement (Planned Phases):**

```python
# User query
query = "Show me all security threats related to our API authentication"

# BrainCell will do (Phase 1-3):
1. Converts query to vector
2. Searches Weaviate for semantically similar items
3. Combines with keyword search (full-text)
4. Retrieves:
   - Threats about API auth
   - Conversations about API design
   - Code snippets in auth modules
   - Decisions about security standards
5. Reranks by relevance
6. Returns ranked results

# User gets: Comprehensive, interconnected knowledge
# Instead of: Scattered, hard-to-find information
```

---

## Why This Matters for BrainCell

**Right now (v0.1.0):** If you ask "What security threats are in our system?" 
- You get threats tagged "security"
- You miss related conversations, code, decisions

**With RAG (Planned):** If you ask "What security threats are in our system?"
- You get threats + related architecture decisions + code snippets + conversations
- All ranked by relevance
- **Automatic knowledge synthesis**

---

## Implementation Roadmap

See [08-AI-KNOWLEDGE-SYSTEMS.md](08-AI-KNOWLEDGE-SYSTEMS.md) for the full 3-phase implementation roadmap:

### **Phase 1 (Weeks 1-4): Foundation**
- Implement hybrid search (semantic + keyword)
- Add query expansion
- Format-aware chunking for code snippets

### **Phase 2 (Weeks 5-8): Smart Discovery**
- Entity extraction (people, systems, vulnerabilities, files)
- Faceted search with filters
- Expertise location service

### **Phase 3 (Weeks 9-16): Knowledge Graph**
- Relationship mapping
- Inference engine
- Cross-linking between cells

---

## Technical Architecture

### **SearchService (Phase 1)**

```python
# Not yet implemented - planned for Phase 1

class SearchService:
    """Unified search across cell types."""
    
    async def semantic_search(
        self,
        query: str,
        cell_types: List[str],
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Search using vector embeddings.
        Returns semantically similar results.
        """
        pass
    
    async def hybrid_search(
        self,
        query: str,
        cell_types: List[str],
        semantic_weight: float = 0.6,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Combine semantic + keyword search.
        semantic_weight: 0.0-1.0 balance between semantic and keyword.
        """
        pass
    
    async def search_with_reranking(
        self,
        query: str,
        cell_types: List[str],
        limit: int = 5,
        rerank_model: str = "cross-encoder"
    ) -> List[SearchResult]:
        """
        Search with intelligent reranking.
        Returns most relevant results first.
        """
        pass
```

### **Query Expansion (Phase 1)**

```python
# Not yet implemented - planned for Phase 1

class QueryExpander:
    """Expand user queries for better retrieval."""
    
    async def expand_query(query: str) -> List[str]:
        """
        Transform:
        "JWT vs sessions" → [
            "JWT vs sessions",
            "JSON Web Token compared to session management",
            "stateless authentication versus stateful sessions",
            "microservices authentication patterns"
        ]
        """
        pass
```

### **Entity Extraction (Phase 2)**

```python
# Not yet implemented - planned for Phase 2

class EntityExtractor:
    """Extract and link entities from text."""
    
    async def extract_entities(text: str) -> EntityMentions:
        """
        From: "SQL injection in login form via Rails"
        Extract: 
          - Vulnerability: SQL injection
          - Component: login form
          - Technology: Rails
          - Type: code vulnerability
        """
        pass
```

### **Knowledge Graph (Phase 3)**

```python
# Not yet implemented - planned for Phase 3

class KnowledgeGraphService:
    """Build and query relationships between entities."""
    
    async def add_relationship(
        source: Entity,
        relation: str,
        target: Entity
    ):
        """
        Example:
        SQLInjection --[affects]--> LoginForm
        LoginForm --[implemented-in]--> Authentication
        """
        pass
    
    async def infer_relationships(
        source: Entity,
        depth: int = 2
    ) -> List[Path]:
        """Find indirect relationships through graph."""
        pass
```

---

## Current Implementation Status

| Component | Status | Location |
|-----------|--------|----------|
| Weaviate Integration | ✅ Ready | `services/weaviate_service.py` |
| Memory Cells | ✅ Ready | `cells/` |
| Database ORM | ✅ Ready | `core/models.py` |
| **SearchService** | 🔧 Planned Phase 1 | `services/search_service.py` |
| **Query Expander** | 🔧 Planned Phase 1 | `services/query_expander.py` |
| **Entity Extractor** | 🔧 Planned Phase 2 | `services/entity_extractor.py` |
| **Knowledge Graph** | 🔧 Planned Phase 3 | `services/knowledge_graph.py` |

---

## Integration with Cells

RAG features will integrate seamlessly:

```python
# Example: Threats cell search
from itl_braincell_sdk.services.search_service import SearchService

search = SearchService()

# Find threats related to user's query
results = await search.hybrid_search(
    query="authentication vulnerabilities",
    cell_types=["threats", "codebase", "architecture", "conversations"],
    semantic_weight=0.7
)

# Returns Threat, CodeSnippet, Conversation objects
# All ranked by relevance
```

---

## Resources

- **Framework docs:** [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://docs.sqlalchemy.org/)
- **Vector DB:** [Weaviate Docs](https://weaviate.io/developers/weaviate)
- **Embeddings:** [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings), [Hugging Face](https://huggingface.co/models?pipeline_tag=sentence-similarity)
- **Reranking:** [Cross-Encoder Models](https://www.sbert.net/examples/applications/cross-encoders/README.html)
- **RAG Papers:** [Relevant papers on retrieval-augmented generation](https://arxiv.org/search/?query=retrieval+augmented+generation)

---

## Questions?

- See [08-AI-KNOWLEDGE-SYSTEMS.md](08-AI-KNOWLEDGE-SYSTEMS.md) for feature priority and roadmap
- See [04-API-REFERENCE.md#search-service-roadmap](04-API-REFERENCE.md) for planned API
- See [Troubleshooting](06-TROUBLESHOOTING.md) for common issues
