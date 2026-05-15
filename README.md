<div align="center">

# Synapse — AI Knowledge Base

**A full-stack RAG platform that lets you chat with your documents, search the web, and collaborate on shared knowledge bases — all through a sleek glassmorphism UI.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Celery](https://img.shields.io/badge/Celery-5.3+-37814A?style=flat-square&logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[Features](#features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [RBAC](#role-based-access-control) · [API Reference](#api-reference) · [Configuration](#configuration)

</div>

---

## Overview

**Synapse** is a self-correcting RAG (Retrieval-Augmented Generation) system that transforms your documents into a searchable intelligence layer. It combines **hybrid FAISS + BM25 retrieval**, an **Advanced RAG brain** with query optimization, **live web search**, **async document indexing via Celery**, and a full **role-based access control** system for team collaboration — all streaming in real time through a polished glassmorphism interface.

```
┌──────────────────────────────────────────────────────────────┐
│                    Synapse — at a glance                      │
│                                                              │
│  Upload docs (PDF / DOCX / TXT / MD / XLSX)                  │
│    → Async-indexed via Celery + Redis (or BackgroundTasks)   │
│  Simple RAG       → FAISS + BM25 hybrid search               │
│  Advanced RAG     → Query optimization + precision pull       │
│  Web Search       → Serper (Google) + DuckDuckGo fallback    │
│  Summarizer       → Chunked AI summarization                 │
│  RBAC             → Owner / Editor / Viewer per KB + Admin   │
└──────────────────────────────────────────────────────────────┘
```

---

## Features

### Chat & RAG
- **Knowledge Base Chat** — Ask questions across one or more knowledge bases using hybrid retrieval
- **Advanced RAG** — Multi-step pipeline: query optimization → precision FAISS retrieval → reranking
- **Web Search** — Live Serper (Google) / DuckDuckGo search woven into answers
- **Streaming Responses** — Real-time NDJSON token-by-token output
- **RAG Pipeline Visualizer** — Live numbered step-by-step progress card during retrieval
- **Citation Chips** — Source pills with document name + color-coded relevance score
  - 🟢 ≥ 85 % · 🟡 70–84 % · 🔴 < 70 %
- **Skeleton Loaders** — Shimmer placeholders while the model is retrieving
- **Session Memory** — Persistent conversation history across browser sessions

### Knowledge Management
- **Multiple Knowledge Bases** — Create, switch, and query multiple KBs at once
- **Async Document Indexing** — Celery workers process uploads in the background with automatic retry; falls back to FastAPI BackgroundTasks when Redis is not available
- **Document Upload** — Ingest PDF, DOCX, DOC, TXT, Markdown, XLSX (chunked + embedded in background)
- **Document Preview** — Read source files inline without leaving the chat
- **Summarizer** — Paste text or upload a file to get a summary + key takeaways
- **FAISS Quantization** — Optional 8-bit scalar quantization (4× memory reduction, ~1 % recall loss)

### Collaboration & Access Control
- **Role-Based Access Control (RBAC)** — Two-layer permission system
  - Global roles: `admin` / `user`
  - Per-KB roles: `owner` / `editor` / `viewer`
- **KB Sharing** — Owners invite teammates by username with a specific role
- **Admin Panel** — User management, role promotion/demotion, system-wide stats
- **First-user Admin** — The first registered account automatically gets `admin` role
- **Permission guards** — Every API route enforces the minimum required role

### LLM Providers

| Provider | Notes |
|---|---|
| **Groq** | Default — fast Llama 3.1 inference (free tier available) |
| **OpenAI** | GPT-4o Mini and above |
| **Google Gemini** | Gemini 2.0 Flash (free tier + 1 M context) |
| **NVIDIA NIM** | Meta Llama via NVIDIA cloud API |
| **AWS Bedrock** | Claude 3 Haiku and other foundation models |
| **Ollama** | Fully local — no API key required |

### UI / UX
- Glassmorphism dark-first design with aurora blue-violet gradient
- Light / Dark theme toggle (persisted)
- Settings page with tabbed navigation — **LLM Providers · Web Search · Account**
- Collapsible sidebar with session management and Admin nav item (visible to admins only)
- Role pills on KB cards; Share modal for member management; role-gated upload/delete controls

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.110+ |
| Server | Uvicorn (async) |
| Database | SQLite via SQLAlchemy async (PostgreSQL-ready) |
| Auth | JWT (PyJWT) + bcrypt |
| Task Queue | Celery 5.3+ with Redis broker |
| Vector Store | FAISS-CPU (flat + optional SQ8/SQ4 quantization) |
| Keyword Search | BM25 (rank-bm25) |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| LLM Orchestration | LangChain + LangGraph |
| Web Search | DuckDuckGo Search / Serper API |
| File Parsing | pdfplumber, python-docx, pandas |
| Encryption | AES-256-GCM (API keys at rest) |

### Frontend

| Layer | Technology |
|---|---|
| Framework | React 18 |
| Build Tool | Vite 5 |
| HTTP Client | Axios |
| Styling | Pure CSS with design tokens (no CSS framework) |

---

## Project Structure

```
KnowledgeBase/
├── src/                              # FastAPI backend
│   ├── main.py                       # App factory, lifespan, schema migrations
│   ├── api/
│   │   ├── auth.py                   # Register / login / JWT (first-user admin)
│   │   ├── chat.py                   # Streaming chat endpoint (NDJSON)
│   │   ├── knowledge_base.py         # KB CRUD + member management endpoints
│   │   ├── documents.py              # Upload, list, delete, summarize
│   │   └── admin.py                  # Admin-only: users, roles, stats
│   ├── worker/
│   │   ├── celery_app.py             # Celery app factory (reads settings)
│   │   └── tasks/indexing.py         # index_document Celery task (retry logic)
│   ├── application/
│   │   ├── rag_service.py            # SelfCorrectingRAG orchestrator
│   │   └── hybrid_retriever.py       # FAISS + BM25 + RRF fusion
│   ├── core/
│   │   ├── settings.py               # Pydantic settings (reads .env)
│   │   ├── search/                   # Query processor, reranker, web search
│   │   └── services/summarizer.py    # Chunked AI summarizer
│   ├── infrastructure/
│   │   ├── adapters/                 # LLM, FAISS, BM25, DB adapters
│   │   └── database/
│   │       ├── models.py             # ORM: User, KnowledgeBase, Document,
│   │       │                         #      ChatSession, Message, KBMember
│   │       └── repositories.py       # Typed repos incl. KBMemberRepository
│   └── shared/
│       ├── rbac.py                   # ROLE_ORDER, require_admin, require_kb_role
│       ├── encryption.py             # AES-256-GCM for API keys
│       └── security.py              # JWT helpers
│
├── web/                              # React frontend
│   └── src/
│       ├── pages/
│       │   ├── Chat.jsx              # Main chat interface + RAG controls
│       │   ├── KnowledgeBase.jsx     # KB management + Share modal
│       │   ├── Settings.jsx          # Tabbed settings (LLM / Web Search / Account)
│       │   └── AdminPage.jsx         # Admin panel: user table + stats
│       ├── components/
│       │   ├── Sidebar.jsx           # Nav with Admin item for admins
│       │   ├── AuthPage.jsx
│       │   ├── SummarizerPage.jsx
│       │   └── ErrorBoundary.jsx
│       ├── hooks/
│       │   ├── useDocuments.js       # Module-level cache (instant re-nav)
│       │   └── useRAGQuery.js        # Streaming fetch + NDJSON parser
│       └── api/
│           ├── documentApi.js        # KB, document, member API calls
│           └── adminApi.js           # Admin API calls
│
├── data_storage/                     # Auto-created at runtime
│   ├── knowledge_base.db             # SQLite database
│   ├── uploads/                      # Uploaded source files
│   └── indices/                      # FAISS + BM25 index files
│
├── docker-compose.yml                # Redis + backend + Celery worker + frontend
├── Dockerfile.backend
├── requirements.txt
└── .env                              # API keys & config (see setup)
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- At least one LLM API key **or** Ollama running locally
- Redis (optional — only needed for Celery; omit for BackgroundTasks mode)

### 1 — Clone & install backend

```bash
git clone <repo-url>
cd KnowledgeBase

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2 — Configure environment

Copy `.env.example` to `.env` and fill in your values:

```env
# ── Security (required) ────────────────────────────────────
JWT_SECRET=your-secure-256-bit-secret-here
ENCRYPTION_KEY=your-64-char-hex-key-here   # python -c "import secrets; print(secrets.token_hex(32))"

# ── LLM Provider (pick at least one) ──────────────────────
GROQ_API_KEY=gsk_...          # https://console.groq.com  (free tier)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...        # https://aistudio.google.com  (free tier)

# ── Web Search (optional) ──────────────────────────────────
SERPER_API_KEY=...            # Leave blank → DuckDuckGo fallback

# ── Celery (optional — leave blank for BackgroundTasks) ────
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ── CORS ───────────────────────────────────────────────────
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3 — Start the backend

```bash
uvicorn src.main:app --reload --port 8000
```

Interactive API docs: `http://localhost:8000/docs`

### 4 — (Optional) Start Celery worker

Only needed if `CELERY_BROKER_URL` is set. Without it, document indexing runs as FastAPI BackgroundTasks.

```bash
# Requires Redis to be running
celery -A src.worker.celery_app.celery_app worker --loglevel=info --concurrency=2
```

### 5 — Start the frontend

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`

### 6 — First run

1. **Register** — the first account automatically becomes **admin**
2. Go to **Settings → LLM Providers** → enter your API key → Save & Activate
3. Go to **Knowledge Base** → create a KB → upload documents
4. Go to **Chat** → select your KB → ask questions

---

## Docker Compose

Starts Redis + FastAPI backend + Celery worker + React frontend in one command:

```bash
cp .env.example .env   # fill in JWT_SECRET and at least one API key
docker compose up --build
```

| Service | Port | Description |
|---|---|---|
| `redis` | 6379 | Celery broker + result backend |
| `backend` | 8000 | FastAPI + Uvicorn |
| `celery_worker` | — | Async document indexing |
| `frontend` | 3000 | React (Vite production build) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Frontend :5173                         │
│                                                                  │
│  AuthPage → App.jsx → Sidebar + Chat / KB / Settings / Admin    │
│                                                                  │
│  Chat.jsx                                                        │
│  ├─ RAG controls (KB selector, Advanced RAG, Web Search)         │
│  ├─ PipelineProgress (live step visualizer)                      │
│  └─ Citation chips (source + relevance %)                        │
│                                                                  │
│  KnowledgeBase.jsx                                               │
│  ├─ Role pills (owner / editor / viewer)                         │
│  ├─ Share modal → member invite + role management                │
│  └─ Upload / delete gated by role                                │
│                                                                  │
│  AdminPage.jsx                                                   │
│  └─ Stats cards + user table (promote / demote)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │  REST + NDJSON streaming (Axios + JWT)
┌───────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend :8000                          │
│                                                                  │
│  RBAC middleware                                                  │
│  ├─ require_admin()       → global admin guard                   │
│  └─ require_kb_role()     → per-KB role guard (admins bypass)    │
│                                                                  │
│  POST /api/chat  (streaming NDJSON)                              │
│  ├─ JWT auth + KB viewer check                                   │
│  ├─ Resolve LLM adapter (per-user provider + key)                │
│  ├─ Optional: WebSearch → inject results into context            │
│  ├─ SelfCorrectingRAG.answer(query, context)                     │
│  │   ├─ HybridRetriever → FAISS + BM25 + RRF fusion              │
│  │   ├─ LLM.chat(system + context + query)                       │
│  │   └─ confidence_score < threshold → retry                     │
│  └─ Stream: status → content → meta (sources, confidence)        │
│                                                                  │
│  POST /api/kb/{id}/documents  (upload)                           │
│  └─ editor+ check → save file → dispatch to Celery / BG task    │
└──────────────────┬──────────────────────────────────────────────┘
                   │
      ┌────────────┴──────────────────────────────┐
      │                                           │
┌─────▼──────┐  ┌───────────────────────────────────────────────┐
│  SQLite DB │  │            Celery Worker                       │
│  users     │  │  index_document task                           │
│  kb_members│  │  ├─ extract text (PDF/DOCX/TXT/XLSX)           │
│  knowledge │  │  ├─ chunk + embed (SentenceTransformer)        │
│  _bases    │  │  ├─ build FAISS + BM25 index                   │
│  documents │  │  └─ update DB status (indexed / failed)        │
│  sessions  │  │  max_retries=2, retry_delay=30s                │
│  messages  │  └───────────────────────────────────────────────┘
└────────────┘
```

---

## Role-Based Access Control

### Permission Matrix

| Action | Viewer | Editor | Owner | Admin |
|--------|:------:|:------:|:-----:|:-----:|
| Chat with KB / view documents | ✅ | ✅ | ✅ | ✅ |
| Upload / delete documents | ❌ | ✅ | ✅ | ✅ |
| Delete KB | ❌ | ❌ | ✅ | ✅ |
| Manage members (invite / remove / change role) | ❌ | ❌ | ✅ | ✅ |
| View all users | ❌ | ❌ | ❌ | ✅ |
| Change global user roles | ❌ | ❌ | ❌ | ✅ |
| Access any KB regardless of membership | ❌ | ❌ | ❌ | ✅ |

### How it works

- **Global role** (`user` / `admin`) is stored on `User.role`. The **first registered user** automatically becomes admin.
- **Per-KB role** (`viewer` / `editor` / `owner`) is stored in the `KBMember` join table. Creating a KB auto-enrolls the creator as owner.
- Admin users bypass all per-KB membership checks — they can access everything.
- Existing knowledge bases are **auto-migrated** on startup: every KB gets an owner `KBMember` record for its creator.

### Sharing a Knowledge Base

1. Open **Knowledge Base** → select a KB you own
2. Click the 👥 icon beside the KB name
3. In the Share modal: type a username, pick a role, click **Invite**
4. Members can be re-roled or removed at any time

---

## Async Document Indexing

Documents are indexed asynchronously so uploads return instantly.

### With Celery + Redis (recommended for production)

Set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` in `.env`:

```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

Start the worker:

```bash
celery -A src.worker.celery_app.celery_app worker --loglevel=info --concurrency=2
```

Features: persistent queue, survives server restarts, automatic retry (up to 2× with 30 s delay), per-task status tracking.

### Without Redis (BackgroundTasks fallback)

Leave both `CELERY_*` vars empty. Indexing runs inside FastAPI's `BackgroundTasks` — zero extra infrastructure, fine for local development.

### FAISS Quantization

Reduce memory footprint of large FAISS indices:

```env
FAISS_QUANTIZE=true
FAISS_QUANTIZE_TYPE=sq8   # sq8 = 8-bit (4× reduction, ~1% recall loss)
                           # sq4 = 4-bit (8× reduction, ~3% recall loss)
```

Set `FAISS_QUANTIZE=false` to use raw float32 `IndexFlatL2`.

---

## Chat Modes

| Mode | What happens |
|---|---|
| No KB selected | General LLM chat (no retrieval) |
| KB selected | Simple RAG — FAISS + BM25 hybrid search |
| KB + Advanced RAG | Query optimization → precision retrieval → reranking |
| + Web Search | Augments any mode with live search results |

### NDJSON stream format

Each line from `POST /api/chat` is a JSON object:

```json
{ "type": "session", "session_id": 42 }
{ "type": "status",  "content": "🔍 Searching knowledge base..." }
{ "type": "content", "delta": "According to " }
{ "type": "meta",    "session_id": 42, "sources": [...] }
{ "type": "error",   "content": "..." }
```

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account, returns JWT + role |
| `POST` | `/auth/login` | Login, returns JWT + role |
| `GET` | `/auth/me` | Current user profile (includes `role`) |
| `GET/POST` | `/auth/settings` | Read / update user settings |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Streaming chat (NDJSON) |
| `GET` | `/api/sessions` | List chat sessions |
| `POST` | `/api/sessions` | Create session |
| `DELETE` | `/api/sessions/{id}` | Delete session |
| `GET` | `/api/models` | List models for active provider |

### Knowledge Bases & Documents

| Method | Endpoint | Min Role | Description |
|---|---|---|---|
| `GET` | `/api/kb` | — | List KBs the caller is a member of |
| `POST` | `/api/kb` | — | Create KB (caller becomes owner) |
| `GET` | `/api/kb/{id}` | viewer | Get KB detail |
| `DELETE` | `/api/kb/{id}` | owner | Delete KB + all documents |
| `GET` | `/api/kb/{id}/documents` | viewer | List documents |
| `POST` | `/api/kb/{id}/documents` | editor | Upload file |
| `DELETE` | `/api/documents/{id}` | editor | Delete document |
| `GET` | `/api/documents/{id}/file` | viewer | Download source file |
| `POST` | `/api/summarize` | — | Summarize text |
| `POST` | `/api/summarize/file` | — | Upload + summarize file |

### KB Members

| Method | Endpoint | Min Role | Description |
|---|---|---|---|
| `GET` | `/api/kb/{id}/members` | viewer | List members + roles |
| `POST` | `/api/kb/{id}/members` | owner | Invite user by username |
| `PUT` | `/api/kb/{id}/members/{uid}` | owner | Change member role |
| `DELETE` | `/api/kb/{id}/members/{uid}` | owner | Remove member |

### Admin (admin role required)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/users` | Paginated user list |
| `PUT` | `/api/admin/users/{id}/role` | Promote / demote user |
| `GET` | `/api/admin/stats` | Total users / KBs / documents |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `JWT_SECRET` | dev default | **Change in production** |
| `ENCRYPTION_KEY` | — | 64-char hex key for API key encryption at rest |
| `DATABASE_URL` | `sqlite:///data_storage/knowledge_base.db` | SQLite or PostgreSQL URL |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `CELERY_BROKER_URL` | `""` | Redis URL — leave empty for BackgroundTasks |
| `CELERY_RESULT_BACKEND` | `""` | Redis URL for task results |
| `FAISS_QUANTIZE` | `true` | Enable SQ8 quantization |
| `FAISS_QUANTIZE_TYPE` | `sq8` | `sq8` or `sq4` |
| `GROQ_API_KEY` | — | Groq API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model |
| `GEMINI_API_KEY` | — | Google Gemini key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model |
| `NVIDIA_API_KEY` | — | NVIDIA NIM key |
| `AWS_ACCESS_KEY_ID` | — | AWS credentials |
| `SERPER_API_KEY` | — | Google Search via Serper (optional) |
| `EMBEDDER_MODEL` | `all-MiniLM-L6-v2` | Sentence Transformer model |
| `CONFIDENCE_THRESHOLD` | `0.5` | Min RAG score before retry |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `DEBUG` | `false` | FastAPI debug mode |

---

## Supported File Types

| Format | Parser |
|---|---|
| `.pdf` | pdfplumber (fallback: PyPDF2) |
| `.docx` / `.doc` | python-docx |
| `.xlsx` / `.xls` | pandas + openpyxl |
| `.txt` / `.md` | Built-in |

Files are indexed asynchronously — the upload endpoint returns immediately while chunking, embedding, and FAISS/BM25 indexing happen in the background.

---

## Development

```bash
# Backend with hot reload
uvicorn src.main:app --reload --port 8000

# Celery worker (separate terminal, needs Redis)
celery -A src.worker.celery_app.celery_app worker --loglevel=info

# Frontend with HMR
cd web && npm run dev

# Run tests
pytest tests/ -v

# Production frontend build
cd web && npm run build   # outputs to web/dist/
```

### Adding a new LLM provider

1. Create `src/infrastructure/adapters/myprovider_llm_adapter.py` implementing `LLMPort`
2. Add a branch in `src/infrastructure/adapters/llm_provider_factory.py`
3. Add static fallback models in `src/api/chat.py`
4. Add the provider tab to `web/src/pages/Settings.jsx`

---

## Roadmap

- [x] Streaming responses (NDJSON)
- [x] Hybrid FAISS + BM25 retrieval with RRF fusion
- [x] Advanced RAG (query optimization + reranking)
- [x] Multi-KB search
- [x] Live web search (Serper + DuckDuckGo)
- [x] RAG pipeline step visualizer
- [x] Citation chips with relevance scores
- [x] Skeleton loaders
- [x] Settings page tabs
- [x] API key encryption at rest (AES-256-GCM)
- [x] Async document indexing with Celery + Redis
- [x] FAISS quantization (SQ8/SQ4)
- [x] Role-based access control (Admin / Owner / Editor / Viewer)
- [x] KB sharing & member management
- [x] Admin panel (user list, role management, system stats)
- [x] Docker Compose (Redis + backend + Celery + frontend)
- [ ] OCR for scanned PDFs
- [ ] Multimodal RAG (images in documents)
- [ ] Export chat history (PDF / Markdown)
- [ ] Email invitations for KB sharing

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with FastAPI · React · LangChain · FAISS · Sentence Transformers · Celery

</div>
