<div align="center">

# Synapse — AI Knowledge Base

**A full-stack RAG platform that lets you chat with your documents, search the web, and summarize content — all through a sleek glassmorphism UI.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[Features](#features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [API Reference](#api-reference) · [Configuration](#configuration)

</div>

---

## Overview

**Synapse** is a self-correcting RAG (Retrieval-Augmented Generation) system that transforms your documents into a searchable intelligence layer. It combines **hybrid FAISS + BM25 retrieval**, an **Advanced RAG brain** with query optimization, and **live web search** — all streaming in real time through a polished glassmorphism interface.

```
┌──────────────────────────────────────────────────────────┐
│                   Synapse — at a glance                   │
│                                                          │
│  Upload docs (PDF / DOCX / TXT / MD)                     │
│    → Auto-indexed into FAISS + BM25                      │
│  Simple RAG       → FAISS + BM25 hybrid search           │
│  Advanced RAG     → Query optimization + precision pull   │
│  Web Search       → Serper (Google) + DuckDuckGo fallback │
│  Summarizer       → Chunked AI summarization             │
└──────────────────────────────────────────────────────────┘
```

---

## Features

### Chat & RAG
- **Knowledge Base Chat** — Ask questions across one or more knowledge bases using hybrid retrieval
- **Advanced RAG** — Multi-step pipeline: query optimization → precision FAISS retrieval → reranking
- **Web Search** — Live Serper (Google) / DuckDuckGo search woven into answers
- **Streaming Responses** — Real-time NDJSON token-by-token output via Server-Sent Events
- **RAG Pipeline Visualizer** — Live numbered step-by-step progress card during retrieval
- **Citation Chips** — Source pills with document name + color-coded relevance score
  - 🟢 ≥ 85 % · 🟡 70–84 % · 🔴 < 70 %
- **Skeleton Loaders** — Shimmer placeholders while the model is retrieving
- **Session Memory** — Persistent conversation history across browser sessions

### Knowledge Management
- **Multiple Knowledge Bases** — Create and switch between isolated KBs; query multiple KBs at once
- **Document Upload** — Ingest PDF, DOCX, DOC, TXT, Markdown (indexed in background)
- **Document Preview** — Read source files inline without leaving the chat
- **Summarizer** — Paste text or upload a file to get a summary + key takeaways

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
- Collapsible sidebar with session management

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.110+ |
| Server | Uvicorn (async) |
| Database | SQLite via SQLAlchemy (async) |
| Auth | JWT (PyJWT) + bcrypt |
| Vector Store | FAISS (CPU) |
| Keyword Search | BM25 (rank-bm25) |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| LLM Orchestration | LangChain + LangGraph |
| Web Search | DuckDuckGo Search / Serper API |
| File Parsing | pdfplumber, python-docx, pandas |

### Frontend

| Layer | Technology |
|---|---|
| Framework | React 18 |
| Build Tool | Vite 5 |
| Routing | React Router v6 |
| HTTP Client | Axios |
| Styling | Pure CSS with design tokens (no CSS framework) |

---

## Project Structure

```
KnowledgeBase/
├── src/                             # FastAPI backend
│   ├── main.py                      # App factory & lifespan
│   ├── api/
│   │   ├── auth.py                  # Register / login / JWT
│   │   ├── chat.py                  # Streaming chat endpoint (NDJSON)
│   │   ├── knowledge_base.py        # KB CRUD
│   │   └── documents.py             # Upload, list, delete, summarize
│   ├── application/
│   │   ├── rag_service.py           # SelfCorrectingRAG orchestrator
│   │   └── hybrid_retriever.py      # FAISS + BM25 + RRF fusion
│   ├── core/
│   │   ├── settings.py              # Pydantic settings (reads .env)
│   │   ├── search/                  # Query processor, reranker, web search
│   │   └── services/summarizer.py   # Chunked AI summarizer
│   ├── infrastructure/
│   │   ├── adapters/                # LLM, FAISS, BM25, DB adapters
│   │   └── database/                # SQLAlchemy ORM models & repositories
│   └── shared/                      # CORS, middleware, exceptions
│
├── web/                             # React frontend
│   └── src/
│       ├── pages/
│       │   ├── Chat.jsx             # Main chat interface + RAG controls
│       │   ├── KnowledgeBase.jsx    # KB & document management
│       │   └── Settings.jsx         # Tabbed settings (LLM / Web Search / Account)
│       ├── components/
│       │   ├── Sidebar.jsx
│       │   ├── AuthPage.jsx
│       │   ├── SummarizerPage.jsx
│       │   ├── PipelineProgress.jsx # RAG step-by-step visualizer
│       │   └── ErrorBoundary.jsx
│       ├── hooks/
│       │   └── useRAGQuery.js       # Streaming fetch + NDJSON parser
│       ├── api/httpClient.js        # Axios instance with auth interceptors
│       └── styles/tokens.css        # Design system tokens
│
├── data_storage/                    # Auto-created at runtime
│   ├── knowledge_base.db            # SQLite database
│   ├── uploads/                     # Uploaded source files
│   └── indices/                     # FAISS + BM25 index files
│
├── requirements.txt
└── .env                             # API keys & config (see setup)
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- At least one LLM API key **or** Ollama running locally

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

Create a `.env` file in the project root:

```env
# ── LLM Provider (pick at least one) ──────────────────────
ACTIVE_PROVIDER=groq          # groq | openai | gemini | nvidia | aws | ollama

GROQ_API_KEY=gsk_...          # https://console.groq.com  (free tier)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...        # https://aistudio.google.com  (free tier)
NVIDIA_API_KEY=nvapi-...

# AWS Bedrock (optional)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Ollama (local, no key needed)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# ── Web Search (optional) ──────────────────────────────────
SERPER_API_KEY=...            # Leave blank → DuckDuckGo fallback

# ── Security ───────────────────────────────────────────────
JWT_SECRET=change-me-in-production

# ── CORS ───────────────────────────────────────────────────
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3 — Start the backend

```bash
uvicorn src.main:app --reload --port 8000
```

Interactive API docs: `http://localhost:8000/docs`

### 4 — Start the frontend

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`

### 5 — First run

1. **Register** an account on first launch
2. Go to **Settings → LLM Providers** → enter your API key → Save & Activate
3. Go to **Knowledge Base** → create a KB → upload documents
4. Go to **Chat** → select your KB → ask questions

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     React Frontend :5173                        │
│                                                                 │
│   AuthPage → App.jsx → Sidebar + Chat / KnowledgeBase / Settings│
│                                                                 │
│   Chat.jsx                                                      │
│   ├─ RAG controls (KB selector, Advanced RAG toggle, Web Search)│
│   ├─ PipelineProgress (live step visualizer)                    │
│   ├─ Skeleton loaders (shimmer during retrieval)                │
│   └─ Citation chips (source + relevance %)                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │  REST + NDJSON streaming (Axios + JWT)
┌───────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend :8000                         │
│                                                                 │
│  POST /api/chat  (streaming NDJSON)                             │
│  ├─ Authenticate (JWT)                                          │
│  ├─ Resolve LLM adapter (per-user provider + key)               │
│  ├─ Optional: WebSearch → inject results into context           │
│  ├─ SelfCorrectingRAG.answer(query, context)                    │
│  │   ├─ HybridRetriever  → FAISS + BM25 + RRF fusion           │
│  │   ├─ LLM.chat(system + context + query)                      │
│  │   └─ confidence_score < threshold → retry                    │
│  └─ Stream: status → content → meta (sources, confidence)       │
│                                                                 │
│  LLMProviderFactory                                             │
│  Groq · OpenAI · Gemini · NVIDIA · AWS Bedrock · Ollama         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────┼──────────────────────┐
          │                 │                      │
   ┌──────▼──────┐  ┌───────▼────────┐  ┌─────────▼──────────┐
   │  SQLite DB  │  │  FAISS Index   │  │  BM25 Index        │
   │  (users,    │  │  (384-dim vecs │  │  (tokenized chunks │
   │   sessions, │  │   per KB)      │  │   per KB)          │
   │   messages) │  └────────────────┘  └────────────────────┘
   └─────────────┘
```

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
{ "type": "status",  "status": "🔍 Searching knowledge base..." }
{ "type": "content", "delta": "According to " }
{ "type": "meta",    "sources": [...], "confidence": 0.91 }
{ "type": "session", "session_id": 42 }
```

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account, returns JWT |
| `POST` | `/auth/login` | Login, returns JWT |
| `GET` | `/auth/me` | Current user profile |
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

| Method | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/api/kb` | List / create knowledge bases |
| `DELETE` | `/api/kb/{id}` | Delete KB + all documents + indices |
| `GET` | `/api/kb/{id}/documents` | List documents |
| `POST` | `/api/kb/{id}/documents` | Upload file (async background indexing) |
| `DELETE` | `/api/documents/{id}` | Delete document |
| `POST` | `/api/summarize` | Summarize text |
| `POST` | `/api/summarize/file` | Upload + summarize file |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ACTIVE_PROVIDER` | `groq` | LLM backend to use |
| `GROQ_API_KEY` | — | Groq API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Groq model |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model |
| `GEMINI_API_KEY` | — | Google Gemini key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model |
| `NVIDIA_API_KEY` | — | NVIDIA NIM key |
| `AWS_ACCESS_KEY_ID` | — | AWS credentials |
| `SERPER_API_KEY` | — | Google Search via Serper (optional) |
| `JWT_SECRET` | dev default | **Change in production** |
| `EMBEDDER_MODEL` | `all-MiniLM-L6-v2` | Sentence Transformer model |
| `CONFIDENCE_THRESHOLD` | `0.5` | Min RAG score before retry |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `DB_URL` | `sqlite:///data_storage/knowledge_base.db` | Database URL |

---

## Supported File Types

| Format | Parser |
|---|---|
| `.pdf` | pdfplumber |
| `.docx` / `.doc` | python-docx |
| `.xlsx` / `.xls` | pandas + openpyxl |
| `.txt` / `.md` | Built-in |

Files are indexed in the background — the upload endpoint returns immediately while chunking, embedding, and FAISS/BM25 indexing happen asynchronously.

---

## Development

```bash
# Backend with hot reload
uvicorn src.main:app --reload --port 8000

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
- [ ] OCR for scanned PDFs
- [ ] Multimodal RAG (images in documents)
- [ ] Export chat history (PDF / Markdown)
- [ ] API key encryption at rest
- [ ] Collaborative knowledge bases

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with FastAPI · React · LangChain · FAISS · Sentence Transformers

</div>
