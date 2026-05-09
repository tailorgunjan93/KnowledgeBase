# Knowledge Base System - RAG Application

A modern RAG-powered knowledge base system with FastAPI backend and React frontend, featuring:
- **Hybrid Retrieval**: FAISS (dense) + BM25 (sparse) with Reciprocal Rank Fusion
- **Anti-Hallucination**: Confidence scoring with source attribution
- **Supervisor-Worker Pattern**: Asynchronous task processing
- **Self-Correction**: Automatic retry on low confidence answers
- **Material-UI**: Modern responsive UI

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Groq API key (free at https://console.groq.com)

### 1. Install Dependencies

```powershell
# Backend - install from pyproject.toml
pip install -r requirements.txt

# Frontend
cd web
npm install
```

### 2. Configure Environment

Edit `.env` file:
```
GROQ_API_KEY=your_groq_api_key
```

### 3. Run Backend

```powershell
python -m uvicorn src.main:app --reload
```

Backend runs at http://localhost:8000

### 4. Run Frontend

```powershell
cd web
npm run dev
```

Frontend runs at http://localhost:3000

## Usage

1. Open http://localhost:3000
2. Go to **Settings** tab - enter your Groq API key
3. Go to **Documents** tab - click "Index Sample Documents"
4. Go to **Query** tab - ask questions like:
   - "What is Python?"
   - "Tell me about machine learning"

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /rag/query | RAG query with anti-hallucination |
| POST | /rag/index | Index documents into hybrid store |
| POST | /chat | Simple chat without RAG |

## Docker Deployment

```powershell
docker-compose up --build
```

## Testing

```powershell
pytest tests/ -v
```

## Architecture

See `architecture.md` for detailed documentation.
