<div align="center">

<img src="https://img.shields.io/badge/KBase-Knowledge%20Base%20AI-6366f1?style=for-the-badge&logo=bookstack&logoColor=white" alt="KBase"/>

# KBase — Knowledge Base AI

**A self-correcting RAG system with multi-provider LLM support, hybrid retrieval, and a clean chat interface.**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](docker-compose.yml)

[Features](#features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [API Reference](#api-reference) · [Configuration](#configuration) · [Docker](#docker-deployment)

</div>

---

## Overview

KBase is a full-stack **Retrieval-Augmented Generation (RAG)** application that lets you build private knowledge bases from your documents and query them in natural language. It combines **hybrid search** (dense FAISS + sparse BM25) with a **self-correcting answer pipeline** and supports **six LLM providers** — switchable per user with no restart required.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KBase — at a glance                         │
│                                                                     │
│   Upload PDFs, DOCX, TXT  →  Auto-indexed into FAISS + BM25        │
│   Ask anything in chat    →  Hybrid retrieval → Self-correcting RAG │
│   Switch LLM anytime      →  Groq / OpenAI / Gemini / NVIDIA /      │
│                               AWS Bedrock / Ollama                  │
│   Web search on demand    →  DuckDuckGo + Wikipedia grounding       │
│   Summarize any document  →  Chunked parallel summarization         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Features

### 🤖 Multi-Provider LLM Support

Six providers, switchable per user from the Settings page. Each provider fetches its available models live from the API, with static fallback lists if credentials aren't set yet.

| Provider | Models | Context | API Key |
|---|---|---|---|
| **Groq** | LLaMA 3.1 8B / 70B, Gemma 2 9B | 128K | `console.groq.com` |
| **OpenAI** | GPT-4o, GPT-4o Mini, o1 Mini | 128K | `platform.openai.com` |
| **Google Gemini** | Gemini 2.0 Flash, 1.5 Pro, 1.5 Flash | **1M** | `aistudio.google.com` |
| **NVIDIA NIM** | Llama 3.3 70B, Nemotron 70B, Mistral 7B | 128K | `build.nvidia.com` |
| **AWS Bedrock** | Claude 3.5 Sonnet, Nova Lite, Llama 3 | 200K | IAM credentials |
| **Ollama** | Any local model (llama3.1, mistral, etc.) | Varies | None — fully local |

> **Tip:** Use **Gemini 1.5 Pro** (1M context) or **AWS Claude 3.5 Sonnet** (200K) for summarizing large documents without chunking errors.

---

### 📚 Knowledge Base Management

- Create multiple isolated knowledge bases per user
- Upload **PDF, DOCX, DOC, TXT, MD, XLSX, XLS** — all parsed automatically in background tasks
- Real-time indexing status (`processing` → `indexed` / `failed`)
- Per-document chunk counts and status badges
- Delete documents and KBs with full cascade cleanup (index files + uploads)

### 🔍 Hybrid Retrieval Pipeline

```
User Query
    │
    ▼
┌───────────────────────────────────────────────────┐
│               Hybrid Retriever                    │
│                                                   │
│  ┌─────────────────┐    ┌──────────────────────┐  │
│  │  Dense Search   │    │   Sparse Search      │  │
│  │  (FAISS)        │    │   (BM25 full-text)   │  │
│  │  all-MiniLM-    │    │   Token matching     │  │
│  │  L6-v2 384-dim  │    │   + TF-IDF scoring   │  │
│  └────────┬────────┘    └──────────┬───────────┘  │
│           │                        │              │
│           └──────────┬─────────────┘              │
│                      ▼                            │
│         Reciprocal Rank Fusion (RRF)              │
│         Top-K merged + re-ranked results          │
└──────────────────────┬────────────────────────────┘
                       │
                       ▼
              Self-Correcting RAG
```

- **Dense retrieval** — `sentence-transformers/all-MiniLM-L6-v2` (384-dim) stored in FAISS
- **Sparse retrieval** — BM25 inverted index for exact keyword matches
- **Reciprocal Rank Fusion** — merges both ranked lists without parameter tuning
- **Confidence scoring** — low-confidence responses trigger auto-retry

### 💬 Chat Interface

- Persistent session history with search and delete
- Web search toggle — enriches answers with live DuckDuckGo + Wikipedia results
- Smart conversational bypass — greetings and short messages skip web search
- Source attribution in responses (which documents were used)
- Confidence badge per answer
- Typing indicator, markdown rendering

### 📝 Document Summarizer

- Summarize uploaded files or pasted text directly in chat
- Parallel chunk summarization for large documents (up to 15 × 12K-char chunks)
- Uses the same user-selected LLM — benefits from large-context providers

### 🔐 Authentication

- JWT-based auth (HS256, 7-day expiration)
- bcrypt password hashing
- Per-user settings stored in DB — each user has their own provider, API keys, and model selection

### 🎨 UI/UX

- Light / Dark theme toggle (persisted)
- Collapsible sidebar with provider status indicator
- Drag-and-drop file upload
- Live model list fetching with Refresh button
- Custom model ID input — type any model not in the list

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        React Frontend :3000                          │
│                                                                      │
│   AuthPage  ─►  App.jsx  ─►  ┌─────────┐ ┌──────────────┐          │
│                               │  Chat   │ │ KnowledgeBase│          │
│                               │  Page   │ │    Page      │          │
│                               └────┬────┘ └──────┬───────┘          │
│                                    │              │                  │
│   Sidebar (sessions, theme,        │    ┌─────────┴───────┐         │
│   provider status)                 │    │  SummarizerPage │         │
│                                    │    └─────────────────┘         │
│                               Settings (6-provider tab UI)          │
└─────────────────────────────────────┬────────────────────────────────┘
                                      │  REST / JSON  (Axios + JWT)
┌─────────────────────────────────────▼────────────────────────────────┐
│                       FastAPI Backend :8000                          │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────────────┐  │
│  │ /auth    │  │ /api/chat│  │ /api/kb   │  │ /api/documents     │  │
│  │ register │  │ sessions │  │ list      │  │ upload (async BG)  │  │
│  │ login    │  │ messages │  │ create    │  │ list / delete      │  │
│  │ settings │  │ POST chat│  │ delete    │  │ /summarize         │  │
│  └──────────┘  └────┬─────┘  └──────────┘  └────────────────────┘  │
│                     │                                               │
│              ┌──────▼──────────────────────────────────┐           │
│              │         SelfCorrectingRAG                │           │
│              │                                          │           │
│              │  1. retrieve(query) via HybridRetriever  │           │
│              │  2. generate(context + query) via LLM    │           │
│              │  3. score(response) → retry if low conf  │           │
│              └──────┬────────────────────┬──────────────┘           │
│                     │                    │                          │
│         ┌───────────▼──────┐   ┌─────────▼────────────────────┐    │
│         │  HybridRetriever │   │    LLMProviderFactory         │    │
│         │  FAISS (dense)   │   │                               │    │
│         │  BM25  (sparse)  │   │  per-request, per-user:       │    │
│         │  RRF fusion      │   │  Groq │ OpenAI │ Gemini       │    │
│         └───────────┬──────┘   │  NVIDIA │ AWS │ Ollama        │    │
│                     │          └──────────────────────────────┘    │
│                     ▼                                               │
│         ┌───────────────────┐                                       │
│         │  WebSearchAdapter │  DuckDuckGo · Wikipedia              │
│         └───────────────────┘                                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
         ┌───────────────────┼─────────────────────────┐
         │                   │                         │
┌────────▼────────┐  ┌───────▼───────┐  ┌─────────────▼──────────────┐
│  SQLite DB      │  │ FAISS Index   │  │ BM25 Index                 │
│  (users, docs,  │  │ (384-dim vecs │  │ (tokenized chunks,         │
│   sessions,     │  │  per KB)      │  │  per KB)                   │
│   messages,     │  └───────────────┘  └────────────────────────────┘
│   settings)     │
└─────────────────┘
```

### Request Flow — Chat Message

```
POST /api/chat  { message, kb_id, enable_web_search }
        │
        ├─ 1. Authenticate (JWT → user)
        ├─ 2. Load LLM adapter   (factory reads user's active_provider + key from DB)
        ├─ 3. Build SelfCorrectingRAG (llm + vector_store)
        ├─ 4. If web_search and not conversational:
        │       └─ WebSearchAdapter.search() → inject into context
        ├─ 5. RAG.answer(query, context)
        │       ├─ HybridRetriever.search() → top-k chunks (FAISS + BM25 + RRF)
        │       ├─ llm.chat([system, context, query])
        │       └─ confidence_score → retry if < threshold
        ├─ 6. Persist ChatMessage (session, role, content, sources)
        └─ 7. Return { response, confidence, sources, session_id }
```

### Document Indexing Flow

```
POST /api/kb/{kb_id}/documents  (multipart file)
        │
        ├─ 1. Save file to data_storage/uploads/{kb_id}/
        ├─ 2. Create Document record (index_status = "processing")
        ├─ 3. Return { id, status: "uploaded" }   ← immediate response
        │
        └─ [Background Task]
              ├─ extract text  (PDF → pdfplumber, DOCX → python-docx, XLSX → pandas)
              ├─ IndexManager.create_document_index(doc_id, content)
              │       ├─ chunk text (500-word chunks, 50-word overlap)
              │       ├─ embed chunks  (SentenceTransformer)
              │       ├─ add to FAISS  + BM25
              │       └─ persist index to data_storage/indices/{kb_id}/
              └─ Update Document (indexed=True, index_status="indexed", chunk_count=N)
```

---

## Quick Start

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.12+ |
| Node.js | 18+ |
| npm / yarn | Latest |
| Git | Any |

> **Optional:** Docker + Docker Compose for containerized deployment.

---

### 1 — Clone & configure

```bash
git clone https://github.com/tailorgunjan93/KnowledgeBase.git
cd KnowledgeBase
cp .env.example .env          # then edit .env
```

Open `.env` and set the required values:

```env
# ── Required ──────────────────────────────────────────────────────────
SECRET_KEY=your-secret-key-here-change-in-production   # JWT signing key

# ── At least one LLM provider ─────────────────────────────────────────
GROQ_API_KEY=gsk_...          # https://console.groq.com  (free tier available)
OPENAI_API_KEY=sk-...         # https://platform.openai.com
GEMINI_API_KEY=AIza...        # https://aistudio.google.com  (free tier available)
NVIDIA_API_KEY=nvapi-...      # https://build.nvidia.com

# AWS Bedrock (optional)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# ── Optional ──────────────────────────────────────────────────────────
ACTIVE_PROVIDER=groq          # Default provider: groq | openai | gemini | nvidia | aws | ollama
CONFIDENCE_THRESHOLD=0.5      # Min confidence before retry
```

---

### 2 — Backend

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Start the API server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at **`http://localhost:8000`**.  
Interactive docs: **`http://localhost:8000/docs`**

---

### 3 — Frontend

```bash
cd web
npm install
npm run dev
```

The app will be available at **`http://localhost:3000`**.

---

### 4 — First run

1. Open `http://localhost:3000` and **register** an account
2. Go to **Settings** → pick your LLM provider → enter API key → click **Save & Activate**
3. Go to **Knowledge Base** → create a KB → upload documents
4. Go to **Chat** → ask questions about your documents

---

## Project Structure

```
KnowledgeBase/
│
├── src/                              # Python backend
│   ├── main.py                       # FastAPI app, lifespan, composition root
│   ├── api/
│   │   ├── auth.py                   # /auth — register, login, settings
│   │   ├── chat.py                   # /api/chat, /api/sessions, /api/models
│   │   ├── knowledge_base.py         # /api/kb — CRUD
│   │   ├── documents.py              # /api/.../documents, /api/summarize
│   │   └── deps.py                   # get_db_session, get_current_user
│   ├── application/
│   │   ├── rag_service.py            # SelfCorrectingRAG
│   │   └── hybrid_retriever.py       # FAISS + BM25 + RRF
│   ├── core/
│   │   ├── settings.py               # Pydantic settings (env-driven)
│   │   ├── search/dynamic_index.py   # IndexManager
│   │   └── services/summarizer.py    # Summarizer + ChunkProcessor
│   ├── domain/
│   │   └── models.py                 # User, Document, KnowledgeBase, ChatSession
│   ├── infrastructure/
│   │   ├── adapters/
│   │   │   ├── groq_llm_adapter.py
│   │   │   ├── openai_llm_adapter.py
│   │   │   ├── gemini_llm_adapter.py
│   │   │   ├── nvidia_llm_adapter.py
│   │   │   ├── aws_llm_adapter.py
│   │   │   ├── ollama_llm_adapter.py
│   │   │   ├── llm_provider_factory.py
│   │   │   ├── faiss_adapter.py
│   │   │   ├── bm25_adapter.py
│   │   │   ├── sentence_transformer_embedder.py
│   │   │   └── web_search_adapter.py
│   │   └── database/
│   │       ├── database.py
│   │       ├── models.py             # SQLAlchemy ORM
│   │       └── repositories.py      # Data access layer
│   ├── ports/
│   │   ├── llm_port.py               # LLMPort protocol (chat + embed)
│   │   └── vector_store_port.py
│   └── shared/
│       ├── security.py               # JWT + bcrypt
│       └── exceptions.py
│
├── web/                              # React frontend
│   └── src/
│       ├── App.jsx                   # Router, session management, layout
│       ├── pages/
│       │   ├── Chat.jsx
│       │   ├── KnowledgeBase.jsx
│       │   └── Settings.jsx          # 6-provider tabbed UI
│       ├── components/
│       │   ├── Sidebar.jsx
│       │   ├── SummarizerPage.jsx
│       │   ├── DropZone.jsx
│       │   └── ConfidenceBadge.jsx
│       ├── api/                      # Axios API clients
│       ├── context/                  # AuthContext, ThemeContext
│       └── index.css                 # CSS variables, component styles
│
├── data_storage/                     # Runtime data (git-ignored)
│   ├── knowledge_base.db             # SQLite database
│   ├── uploads/                      # Uploaded source files
│   └── indices/                      # FAISS + BM25 index files
│
├── tests/                            # pytest test suite
├── docker-compose.yml
└── requirements.txt
```

---

## API Reference

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/auth/register` | Create account, returns JWT | — |
| `POST` | `/auth/login` | Login, returns JWT | — |
| `GET` | `/auth/me` | Current user profile | ✓ |
| `GET` | `/auth/settings` | All user settings | ✓ |
| `POST` | `/auth/settings` | Update one setting `{ key, value }` | ✓ |

### Chat

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/sessions` | List chat sessions | ✓ |
| `POST` | `/api/sessions` | Create new session | ✓ |
| `GET` | `/api/sessions/{id}/messages` | Get session messages | ✓ |
| `DELETE` | `/api/sessions/{id}` | Delete session | ✓ |
| `POST` | `/api/chat` | Send message (RAG + optional web search) | ✓ |
| `GET` | `/api/models` | List models for active/specified provider | ✓ |
| `GET` | `/api/llm-provider` | Active provider + credential status | ✓ |

**`POST /api/chat` request body:**
```json
{
  "message": "What does the Q3 report say about revenue?",
  "session_id": 42,
  "kb_id": 1,
  "enable_web_search": false
}
```

**Response:**
```json
{
  "response": "According to the Q3 report, revenue increased by 18%...",
  "confidence": 0.91,
  "sources": ["Q3_Report_2024.pdf (page 3)", "executive_summary.docx"],
  "session_id": 42
}
```

### Knowledge Bases

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/kb` | List user's knowledge bases | ✓ |
| `POST` | `/api/kb` | Create KB `{ name, description }` | ✓ |
| `GET` | `/api/kb/{kb_id}` | KB detail | ✓ |
| `DELETE` | `/api/kb/{kb_id}` | Delete KB + all documents + indices | ✓ |

### Documents

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/kb/{kb_id}/documents` | List documents | ✓ |
| `POST` | `/api/kb/{kb_id}/documents` | Upload file (returns immediately, indexes async) | ✓ |
| `DELETE` | `/api/documents/{doc_id}` | Delete document + index + file | ✓ |
| `POST` | `/api/summarize` | Summarize text `{ text, max_length }` | ✓ |
| `POST` | `/api/summarize/file` | Upload + summarize file | ✓ |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check `{ status: "ok" }` |
| `GET` | `/ready` | Readiness check (DB + model) |
| `GET` | `/docs` | Interactive OpenAPI docs (Swagger UI) |

---

## Configuration

All settings are driven by environment variables (`.env` file or shell environment).  
The `src/core/settings.py` Pydantic model documents every available key.

### Core

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | **required** | JWT signing secret |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_DAYS` | `7` | Token lifetime |
| `DATABASE_URL` | `sqlite+aiosqlite:///data_storage/knowledge_base.db` | Database URL |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed frontend origins |

### LLM Providers

| Variable | Default | Description |
|---|---|---|
| `ACTIVE_PROVIDER` | `groq` | Default provider for new users |
| `GROQ_API_KEY` | — | Groq API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Default Groq model |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Default OpenAI model |
| `GEMINI_API_KEY` | — | Google AI Studio key |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Default Gemini model |
| `NVIDIA_API_KEY` | — | NVIDIA NIM key |
| `NVIDIA_MODEL` | `meta/llama-3.1-8b-instruct` | Default NVIDIA model |
| `AWS_ACCESS_KEY_ID` | — | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | — | AWS secret key |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_MODEL` | `anthropic.claude-3-haiku-20240307-v1:0` | Default Bedrock model |

### RAG & Retrieval

| Variable | Default | Description |
|---|---|---|
| `EMBEDDER_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer model |
| `CONFIDENCE_THRESHOLD` | `0.5` | Min score before retry |
| `MAX_RETRIES` | `2` | Max self-correction retries |
| `TOP_K_RETRIEVAL` | `5` | Number of chunks to retrieve |

---

## LLM Provider Setup

### Groq (Recommended — free tier)

1. Sign up at [console.groq.com](https://console.groq.com)
2. Create an API key
3. In Settings, select **Groq**, enter the key, click **Save & Activate**
4. Models are fetched live — pick from the dropdown

### OpenAI

1. Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Select **OpenAI** tab in Settings, enter key → Save
3. Live model list: GPT-4o, GPT-4o Mini, o1 series

### Google Gemini (free tier + 1M context)

1. Get a free key at [aistudio.google.com](https://aistudio.google.com)
2. Select **Gemini** tab → enter key → Save
3. Use **Gemini 1.5 Pro** for documents up to ~750K words

### NVIDIA NIM

1. Register at [build.nvidia.com](https://build.nvidia.com) — free credits included
2. Select **NVIDIA** tab → enter `nvapi-...` key → Save
3. Access Llama, Mistral, Phi-3, Nemotron and more

### AWS Bedrock

1. Create an IAM user with `bedrock:InvokeModel` and `bedrock:ListFoundationModels` permissions
2. Select **AWS Bedrock** tab → enter Access Key ID + Secret + Region → Save
3. Models fetched live from your account's enabled model list

### Ollama (fully local, no API key)

```bash
# Install Ollama from https://ollama.com
ollama pull llama3.1:8b          # or any model you prefer
ollama serve                      # starts on localhost:11434
```

In Settings, select **Ollama** and enter the model name (e.g. `llama3.1:8b`).  
No API key needed — runs entirely on your machine.

---

## Supported File Types

| Format | Parser | Notes |
|---|---|---|
| `.pdf` | `pdfplumber` / `PyPDF2` | Multi-page, text-only (scanned PDFs need OCR) |
| `.docx` / `.doc` | `python-docx` | Full paragraph extraction |
| `.xlsx` / `.xls` | `pandas` + `openpyxl` | Tabular data converted to string |
| `.txt` / `.md` | Built-in | UTF-8 encoded |
| Other text | Built-in (best-effort) | `errors=ignore` fallback |

Large files are handled automatically:
- Text extracted in background (no request timeout)
- Summarization chunked into 12K-char segments processed in parallel (up to 15 chunks)
- FAISS index persisted to disk for persistence across restarts

---

## Docker Deployment

```bash
# Build and start both services
docker-compose up --build

# Or run detached
docker-compose up -d --build
```

The `docker-compose.yml` starts:
- **backend** — FastAPI on port `8000`, mounts `data_storage/` volume
- **frontend** — Vite dev server on port `3000`

**Production build:**

```bash
cd web && npm run build            # outputs to web/dist/
# Serve web/dist/ via nginx or any static server
```

Sample nginx config for the built frontend + API proxy:

```nginx
server {
    listen 80;

    location /api/ {
        proxy_pass http://localhost:8000;
    }
    location /auth/ {
        proxy_pass http://localhost:8000;
    }
    location / {
        root /path/to/web/dist;
        try_files $uri /index.html;
    }
}
```

---

## Development

### Running tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific module
pytest tests/test_rag_service.py -v
```

### Backend hot reload

```bash
python -m uvicorn src.main:app --reload --port 8000
```

### Frontend dev server

```bash
cd web && npm run dev              # Vite HMR on :3000
```

### Adding a new LLM provider

1. Create `src/infrastructure/adapters/myprovider_llm_adapter.py` implementing `LLMPort`:

```python
class MyProviderLLMAdapter:
    def __init__(self, api_key: str, model: str) -> None:
        ...

    def chat(self, messages: list[dict], max_tokens: int = 1000) -> str:
        ...

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use SentenceTransformerEmbedder")
```

2. Add a branch in `src/infrastructure/adapters/llm_provider_factory.py`
3. Add static fallback models to `_PROVIDER_MODELS` in `src/api/chat.py`
4. Add a live-fetch branch in the `list_models` endpoint
5. Add the provider tab to `web/src/pages/Settings.jsx`

---

## Tech Stack

<table>
<tr>
<td valign="top">

**Backend**
- Python 3.12+
- FastAPI 0.110+
- SQLAlchemy 2.0 (async)
- aiosqlite
- PyJWT + bcrypt
- Pydantic v2

</td>
<td valign="top">

**AI / RAG**
- LangChain + LangGraph
- Sentence Transformers
- FAISS (dense vector)
- rank-bm25 (sparse)
- Groq SDK
- OpenAI SDK
- google-genai
- boto3 (AWS)
- httpx (Ollama)

</td>
<td valign="top">

**Frontend**
- React 18
- Vite 5
- React Router 6
- Axios
- CSS Variables

</td>
<td valign="top">

**Parsing / Search**
- pdfplumber + PyPDF2
- python-docx
- pandas + openpyxl
- duckduckgo-search
- wikipedia

</td>
</tr>
</table>

---

## Roadmap

- [ ] OCR support for scanned PDFs (Tesseract)
- [ ] Streaming responses (SSE / WebSocket)
- [ ] Multi-user knowledge base sharing
- [ ] Re-ranking layer (cross-encoder)
- [ ] Image support in documents
- [ ] Export chat history (PDF / Markdown)
- [ ] API key encryption at rest

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push and open a Pull Request

Please run `pytest` and ensure all tests pass before submitting.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with FastAPI · React · LangChain · FAISS · Sentence Transformers

</div>
