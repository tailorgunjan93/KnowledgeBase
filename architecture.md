# Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    React.js Frontend                        │
│                   (localhost:3000)                         │
└─────────────────────┬───────────────────────────────────────┘
                    │ HTTP/REST
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                         │
│                   (localhost:8000)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Supervisor (Worker Pattern)           │   │
│  │  ┌─────────┐ ┌──────────��� ┌────────────┐        │   │
│  │  │ Document│ │   Chat   │ │  Vector   │ Workers   │   │
│  │  │Worker  │ │ Worker  │ │  Worker  │            │   │
│  │  └─────────┘ └──────────┘ └────────────┘        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    ┌─────────┐ ┌───────┐ ┌─────────┐
    │SQLite  │ │ FAISS │ │Groq API│
    │   DB   │ │ VecDB │ │   LLM  │
    └─────────┘ └───────┘ └─────────┘
```

## Retrieval Components (FAISS + BM25 Hybrid)

```
┌─────────────────────────────────────────────────────────────┐
│              Hybrid Retrieval Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│  User Query                                            │
│       │                                               │
│       ▼                                               │
│  ┌─────────────────────┐                               │
│  │ Sentence          │  (all-MiniLM-L6-v2)              │
│  │ Transformers     │                               │
│  └────────┬──────────┘                               │
│           │                                                  │
│     ┌────┴────┐                                          │
│     ▼         ▼                                             │
│  ┌───────┐ ┌───────┐                                       │
│  │ FAISS │ │ BM25  │  (Parallel search)                      │
│  │ Dense │ │Sparse │                                       │
│  └──┬────┘ └───┬───┘                                       │
│     │          │                                            │
│     └────┬─────┘                                            │
│          ▼                                                   │
│  ┌─────────────────────┐                                     │
│  │ Reciprocal Rank     │  (RRF Fusion)                        │
│  │ Fusion             │                                     │
│  └────────┬──────────┘                                     │
│           │                                                  │
│           ▼                                                  │
│      Top-K Results                                         │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (`web/`)

```
web/
├── src/
│   ├── api.js           # Axios API client
│   ├── App.jsx         # Router + layout
│   ├── pages/
│   │   ├── Chat.jsx    # Chat interface
│   │   ├── KnowledgeBase.jsx  # KB management
│   │   └── Settings.jsx       # Settings
│   └── components/
│       └── Sidebar.jsx
├── vite.config.js       # Vite + proxy config
└── package.json
```

**Responsibilities:**
- UI rendering with React 18
- User interaction handling
- API communication via Axios
- State management (local state)

### 2. Backend (`api/`)

```
api/
├── main.py            # FastAPI app + CORS
└── routes.py         # API endpoints
```

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/rag | RAG chat |
| POST | /api/feedback | Submit feedback |
| GET | /api/knowledge-bases | List KBs |
| POST | /api/documents | Upload doc |
| POST | /api/search | Search vectors |
| GET | /api/sessions/{id} | Chat sessions |
| GET | /api/messages/{id} | Session messages |
| GET | /api/agent-history | ReAct history |

### 3. Application Layer (`src/application/`)

```
src/application/
├── rag_service.py    # Self-correcting RAG
├── chat_usecase.py    # Chat orchestration
└── document_service.py
```

**Key Classes:**

```python
class SelfCorrectingRAG:
    def query(query, user_id, use_react, use_web_search) -> RAGResult
    def apply_feedback(user_id, query, feedback, corrected_answer)
    def calculate_confidence(query, context) -> float

class ReActAgent:
    def execute(query) -> AgentState  # Thought → Action → Observation loop
```

### 4. Infrastructure Layer (`src/infrastructure/`)

```
src/infrastructure/
├── workers/
│   ├── worker.py      # Base Worker + Task
│   └── supervisor.py # Supervisor pattern
├── agents/
│   └── react_agent.py
├── databases/
│   ├── sqlalchemy_repo.py
│   └── faiss_vector_db.py
└── adapters/
    ├── tools_adapter.py    # Wikipedia, Arxiv, DDG
    └── llm_adapter.py
```

**Worker Types:**
- `DocumentWorker` - Parse, extract text from files
- `ChatWorker` - Handle chat requests
- `VectorWorker` - Add/search vectors

### 5. Domain Layer (`src/domain/`)

```
src/domain/
└── models.py
```

**ORM Models:**
- `User` - User accounts
- `ChatSession` - Chat conversations
- `ChatMessage` - Messages
- `KnowledgeBase` - Document collections
- `Document` - Uploaded files
- `Skill` - Custom prompts
- `RAGFeedback` - User feedback
- `AgentHistory` - ReAct execution log

### 6. Core Layer (`src/core/`)

```
src/core/
├── settings.py       # Config loader (JSON + .env)
└── config.py        # Legacy config
```

## Design Patterns

### 1. Supervisor-Worker Pattern

```
┌─────────────┐     ┌─────────────┐
│ Supervisor │────▶│ Task Queue  │
└─────────────┘     └─────────────┘
                          │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │Worker 1 │    │Worker 2 │    │Worker 3 │
    └─────────┘    └─────────┘    └─────────┘
```

**Purpose:** Decouple request handling from execution
- Non-blocking API responses
- Parallel task processing
- Scalable worker pool

### 2. ReAct Agent Pattern

```
Thought: I need to search for this
Action: search_knowledge
Action Input: Python programming
Observation: [results]
Thought: [analysis]
Action: answer
```

**Loop:** Thought → Action → Observation → Reasoning (repeat)

### 3. Self-Correcting RAG

```
Query → Retrieve → Generate → Confidence Check
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
      Score ≥ 0.3               Score < 0.3
            │                         │
            ▼              ┌─────────┴─────────┐
        Return Answer      │ Request Feedback │
                         └─────────────────┘
```

**Feedback Types:**
- `thumbs_up` - Good answer
- `thumbs_down` - Poor answer
- `corrected` - User provides correction

### 4. Settings Injection

```
settings.json          .env (sensitive)
     │                    │
     ▼                    ▼
┌─────────────┐    ┌─────────────┐
│   Public   │    │  Private  │
│   Config  │    │   Config  │
└─────────��───┘    └─────────────┘
       │                  │
       └────────┬────────┘
                ▼
        ┌─────────────┐
        │AppSettings│
        │ (merged)  │
        └─────────────┘
```

## Data Flow

### Chat Request Flow

```
User Input
    │
    ▼
React Frontend ───── HTTP POST /api/rag
    │
    ▼
FastAPI Route ─────── routes.py
    │
    ▼
Supervisor ─────── Queue task
    │
    ▼
ChatWorker ──────── Execute
    │
    ▼
RAG Service ─────── Query + Generate
    │
    ├──▶ Vector Store ── Search
    │
    ├──▶ LLM Adapter ── Generate
    │
    └──▶ Database ──── Save history
    │
    ▼
Response ─────────── JSON
    │
    ▼
React Frontend ───── Display
```

## Security

- API keys stored in `.env` (not in git)
- Database not tracked in git
- JWT for authentication (future)
- Per-user data isolation via user_id

## Anti-Hallucination System

```
┌─────────────────────────────────────────────────────────────┐
│            Anti-Hallucination Pipeline                     │
├─────────────────────────────────────────────────────────────┤
│  Generated Answer                                     │
│       │                                               │
│       ▼                                               │
│  ┌─────────────────────┐                               │
│  │ Source Attribution │                               │
│  └────────┬──────────┘                               │
│           │                                                  │
│           ▼                                               │
│  ┌─────────────────────┐                               │
│  │ Confidence Scoring │                               │
│  │ - Source: 60%     │                               │
│  │ - Consistency:40% │                               │
│  └────────┬──────────┘                               │
│           │                                                  │
│      ┌───┴───┐                                          │
│      ▼       ▼                                            │
│  Score≥0.5  Score<0.5                                    │
│      │       │                                             │
│      ▼       ▼                                            │
│  Return  Self-Correct                                      │
│  Answer (LLM retry)                                      │
└─────────────────────────────────────────────────────────────┘
```

### Confidence Scoring Formula

```
Confidence = 0.6 * source_score + 0.4 * consistency_score

source_score = sum(scores) / len(sources)
consistency_score = overlap(answer_words, source_words) / len(sources)
```

### Self-Correction Loop

- Max retries: 2
- Triggered when confidence < 0.5
- Uses correction prompt with sources
- Validates response length changes

## Testing

```
tests/
├── test_settings.py    # Settings loader
├── test_workers.py   # Worker pattern
├── test_retrieval.py   # FAISS, BM25, Hybrid
└── test_anti_hallucination.py  # Confidence scoring
```

Run tests:
```bash
pytest tests/
```