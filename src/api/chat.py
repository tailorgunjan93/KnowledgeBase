from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

from .deps import get_db_session, get_current_user
from ..infrastructure.database.repositories import ChatSessionRepository, MessageRepository, UserSettingRepository, KnowledgeBaseRepository
from ..domain.models import ChatSession, Message, User, UserSetting, KnowledgeBase

from ..core.settings import get_settings

router = APIRouter(prefix="/api", tags=["chat"])


class CreateSessionRequest(BaseModel):
    kb_id: Optional[int] = None
    title: Optional[str] = "New Chat"


class SessionResponse(BaseModel):
    id: int
    kb_id: Optional[int]
    title: str
    created_at: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    intent: Optional[str] = None
    confidence: Optional[str] = None
    sources: Optional[List[dict]] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    kb_id: Optional[int] = None # Legacy support
    kb_ids: Optional[List[int]] = None
    enable_web_search: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: int
    intent: Optional[str] = None
    confidence: Optional[str] = None
    sources: Optional[List[dict]] = None


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 20
):
    repo = ChatSessionRepository(ChatSession, db)
    sessions = await repo.get_by_user(current_user.id, skip=skip, limit=limit)

    return [
        SessionResponse(
            id=s.id,
            kb_id=s.kb_id,
            title=s.title or "Untitled",
            created_at=s.created_at.isoformat()
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    req: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    repo = ChatSessionRepository(ChatSession, db)

    # Validate kb_id if provided
    if req.kb_id:
        kb_repo = KnowledgeBaseRepository(KnowledgeBase, db)
        if not await kb_repo.get_by_user_and_id(req.kb_id, current_user.id):
            raise HTTPException(404, "Knowledge base not found")

    session = await repo.create(
        user_id=current_user.id,
        kb_id=req.kb_id,
        title=req.title
    )
    await db.commit()

    return SessionResponse(
        id=session.id,
        kb_id=session.kb_id,
        title=session.title or "New Chat",
        created_at=session.created_at.isoformat()
    )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    repo = ChatSessionRepository(ChatSession, db)
    session = await repo.get_by_user_and_id(session_id, current_user.id)

    if not session:
        raise HTTPException(404, "Session not found")

    msg_repo = MessageRepository(Message, db)
    messages = await msg_repo.get_by_session(session_id)

    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            intent=m.intent,
            confidence=m.confidence,
            sources=m.sources
        )
        for m in messages
    ]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    logger.info(f"Chat endpoint called: user={current_user.id}, message_len={len(req.message)}")
    # Get or create session
    session_repo = ChatSessionRepository(ChatSession, db)
    if req.session_id:
        session = await session_repo.get_by_user_and_id(req.session_id, current_user.id)
        if not session:
            raise HTTPException(404, "Session not found")
    else:
        session = await session_repo.create(
            user_id=current_user.id,
            kb_id=req.kb_ids[0] if req.kb_ids and len(req.kb_ids) > 0 else req.kb_id,
            title=req.message[:50] + "..." if len(req.message) > 50 else req.message
        )
        await db.flush()

    # Save user message
    msg_repo = MessageRepository(Message, db)
    await msg_repo.create(
        session_id=session.id,
        role="user",
        content=req.message
    )
    await db.flush()

    # Perform RAG chat using the injected service
    try:
        from fastapi.concurrency import run_in_threadpool
        rag_service = request.app.state.rag_service
        
        context_override = None
        sources_override = None
        
        kb_id = req.kb_ids[0] if req.kb_ids and len(req.kb_ids) > 0 else req.kb_id
        if kb_id:
            from ..core.search.dynamic_index import IndexManager
            from ..infrastructure.database.repositories import DocumentRepository
            from ..domain.models import Document
            
            doc_repo = DocumentRepository(Document, db)
            docs = await doc_repo.get_by_kb(kb_id)
            doc_ids = [d.id for d in docs if d.indexed]
            
            if doc_ids:
                index_mgr = IndexManager(kb_id)
                search_results = await run_in_threadpool(index_mgr.search_kb, req.message, doc_ids, 5)
                
                if search_results:
                    context_override = "\n\n".join([f"Source (Doc {s.get('doc_id')}):\n{s.get('text', '')}" for s in search_results])
                    sources_override = search_results

        if req.enable_web_search:
            try:
                def _run_web_search():
                    import httpx as _httpx
                    combined = []
                    serper_key = get_settings().serper_api_key

                    # 1. Serper (Google Search API) — primary, reliable
                    if serper_key:
                        try:
                            resp = _httpx.post(
                                "https://google.serper.dev/search",
                                headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                                json={"q": req.message, "num": 5},
                                timeout=10,
                            )
                            if resp.status_code == 200:
                                for r in resp.json().get("organic", [])[:5]:
                                    combined.append({"title": r.get("title", ""), "href": r.get("link", ""), "body": r.get("snippet", "")})
                        except Exception as e:
                            logger.warning(f"Serper search failed: {e}")

                    # 2. Wikipedia — great for factual / encyclopedic queries
                    try:
                        import wikipedia
                        wikipedia.set_lang("en")
                        wiki_results = wikipedia.search(req.message, results=3)
                        for title in wiki_results[:2]:
                            try:
                                summary = wikipedia.summary(title, sentences=3, auto_suggest=False)
                                page = wikipedia.page(title, auto_suggest=False)
                                combined.append({"title": title, "href": page.url, "body": summary})
                            except Exception:
                                continue
                    except Exception as e:
                        logger.warning(f"Wikipedia search failed: {e}")

                    if combined:
                        return combined

                    # 3. DuckDuckGo fallback (flaky but free)
                    from duckduckgo_search import DDGS
                    for backend in ("html", "lite", "auto"):
                        try:
                            results = list(DDGS(timeout=12).text(req.message, max_results=5, backend=backend))
                            if results:
                                return results
                        except Exception:
                            continue
                    try:
                        news = list(DDGS(timeout=12).news(req.message, max_results=5))
                        if news:
                            return [{"title": r.get("title", ""), "href": r.get("url", ""), "body": r.get("body", "")} for r in news]
                    except Exception:
                        pass
                    return []
                web_results = await run_in_threadpool(_run_web_search)
                logger.info(f"Web search returned {len(web_results)} results")
                if web_results:
                    web_context = "[WEB SEARCH RESULTS]\n" + "\n\n".join([
                        f"Title: {r.get('title', '')}\nURL: {r.get('href', '')}\n{r.get('body', '')}"
                        for r in web_results
                    ])
                    context_override = (context_override + "\n\n" + web_context) if context_override else web_context
                    web_sources = [
                        {"type": "web", "title": r.get("title", ""), "url": r.get("href", ""), "text": r.get("body", "")}
                        for r in web_results
                    ]
                    sources_override = (sources_override or []) + web_sources
                else:
                    logger.warning("Web search returned 0 results from all backends")
                    no_result_msg = "[WEB SEARCH] Search was attempted but returned no results. Answer based on your training knowledge."
                    context_override = (context_override + "\n\n" + no_result_msg) if context_override else no_result_msg
            except Exception as web_err:
                logger.warning(f"Web search failed: {web_err}")

        result = await run_in_threadpool(rag_service.answer, req.message, context_override, sources_override)

        # Save assistant message
        await msg_repo.create(
            session_id=session.id,
            role="assistant",
            content=result.get("response", ""),
            intent=result.get("intent"),
            confidence=str(result.get("confidence")),
            sources=result.get("sources")
        )
        await db.commit()

        return ChatResponse(
            response=result.get("response", ""),
            session_id=session.id,
            intent=result.get("intent"),
            confidence=str(result.get("confidence")),
            sources=result.get("sources")
        )

    except Exception as e:
        await db.rollback()
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Chat endpoint error: {e}")
        logger.error(f"Full traceback: {error_details}")
        raise HTTPException(500, f"Chat error: {str(e)} - Details: {error_details}")


# --- Known-good Groq models as a fallback when the API key is absent ---
_FALLBACK_MODELS = [
    {"id": "llama-3.1-8b-instant",     "label": "LLaMA 3.1 — 8B Instant (fast)"},
    {"id": "llama-3.1-70b-versatile",  "label": "LLaMA 3.1 — 70B Versatile"},
    {"id": "llama3-8b-8192",           "label": "LLaMA 3 — 8B"},
    {"id": "llama3-70b-8192",          "label": "LLaMA 3 — 70B"},
    {"id": "gemma2-9b-it",             "label": "Gemma 2 — 9B"},
    {"id": "gemma-7b-it",              "label": "Gemma — 7B"},
]

# Chat-compatible Groq models are identified by their id prefix.
_CHAT_PREFIXES = ("llama", "mixtral", "gemma", "whisper", "deepseek", "qwen")


@router.get("/models")
async def list_models(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Return available Groq chat models. Fetches live list when an API key is present."""
    # Prefer the key sent by the frontend; fall back to the user's stored key.
    api_key = x_api_key
    if not api_key:
        repo = UserSettingRepository(UserSetting, db)
        setting = await repo.get_by_user_and_key(current_user.id, "groq_api_key")  # type: ignore[arg-type]
        api_key = str(setting.value) if setting and setting.value else None
    if not api_key:
        api_key = get_settings().groq_api_key

    if not api_key:
        return {"source": "fallback", "models": _FALLBACK_MODELS}

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)
        response = await client.models.list()
        models = [
            {"id": m.id, "label": _make_label(m.id)}
            for m in sorted(response.data, key=lambda m: m.id)
            if "whisper" not in m.id.lower()
        ]
        if not models:
            return {"source": "fallback", "models": _FALLBACK_MODELS}
        return {"source": "groq", "models": models}
    except Exception as exc:
        logger.warning(f"Could not fetch Groq model list: {exc}")
        return {"source": "fallback", "models": _FALLBACK_MODELS}


def _make_label(model_id: str) -> str:
    """Turn a Groq model id like 'llama-3.1-8b-instant' into a readable label."""
    parts = model_id.split("-")
    # capitalise first segment, keep the rest as-is
    return " — ".join([parts[0].capitalize()] + parts[1:]) if parts else model_id


@router.get("/llm-provider")
async def get_llm_provider(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from ..core.settings import get_settings
    from ..services.ollama_service import OllamaService
    
    repo = UserSettingRepository(UserSetting, db)
    setting = await repo.get_by_user_and_key(current_user.id, "groq_api_key")  # type: ignore[arg-type]
    api_key = str(setting.value) if setting and setting.value else None
    
    settings = get_settings()
    if not api_key:
        api_key = settings.groq_api_key

    ollama_running = OllamaService.check_available(settings.ollama_base_url)
    
    active_provider = "none"
    if api_key:
        active_provider = "groq"
    elif ollama_running:
        active_provider = "ollama"
        
    return {
        "active_provider": active_provider,
        "ollama": {
            "available": ollama_running,
            "model": settings.ollama_model
        }
    }
