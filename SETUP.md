# Setup & Run Guide

## Quick Start

### 1. Install Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd web
npm install
```

### 2. Configure API Key

```bash
copy .env.example .env
notepad .env
```

Set your Groq API key:
```
GROQ_API_KEY=your_key_here
```

Get free key at: https://console.groq.com

### 3. Run Backend

```bash
python -m uvicorn backend.main:app --reload
```

Backend runs at: http://localhost:8000

### 4. Run Frontend

```bash
cd web
npm run dev
```

Frontend runs at: http://localhost:5173

---

## Features

| Page | Features |
|------|---------|
| **Login/Signup** | Create account, login |
| **Chat** | AI chat, KB selection, skills, web search, ReAct |
| **Knowledge Base** | Create KB, upload PDF/Word/Excel |
| **Summarizer** | Upload docs, generate summary |
| **Skills** | Create custom AI behaviors |
| **Settings** | API key, theme (light/dark) |

---

## Files

```
app.py              # Main Streamlit app
├── ui/pages/
│   ├── auth_page.py      # Login/Signup
│   ├── chat_page.py     # Chat
│   ├── kb_page.py      # Knowledge Base
│   ├── summarizer_page.py
│   ├── skills_page.py
│   └── settings_page.py
```

---

## Troubleshooting

**Error: No module named 'src'**
```bash
# Set PYTHONPATH
set PYTHONPATH=.
# Or run from project root
```

**Database error:**
```bash
del data_storage\knowledge_base.db
```

**API key error:**
Check `.env` has valid `GROQ_API_KEY`