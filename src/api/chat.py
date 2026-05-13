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


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    repo = ChatSessionRepository(ChatSession, db)
    session = await repo.get_by_user_and_id(session_id, current_user.id)  # type: ignore[arg-type]
    if not session:
        raise HTTPException(404, "Session not found")
    await repo.delete(session_id)
    await db.commit()


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

        _CONVERSATIONAL = {
            "hello", "hi", "hey", "hiya", "howdy", "sup", "yo",
            "thanks", "thank you", "ty", "thx", "cheers",
            "ok", "okay", "sure", "alright", "great", "cool",
            "yes", "no", "maybe", "nope", "yep", "yup",
            "bye", "goodbye", "cya", "see you", "later",
            "good morning", "good afternoon", "good evening", "good night",
            "how are you", "how are you doing", "what's up", "whats up",
        }
        _msg_lower = req.message.strip().lower().rstrip("!?.,")
        _skip_web = _msg_lower in _CONVERSATIONAL or (len(_msg_lower.split()) <= 2 and len(_msg_lower) < 20)

        if req.enable_web_search and not _skip_web:
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

        from ..infrastructure.adapters.llm_provider_factory import get_llm_for_user
        from ..application.rag_service import SelfCorrectingRAG

        try:
            llm = await get_llm_for_user(current_user.id, db)  # type: ignore[arg-type]
        except ValueError as llm_err:
            raise HTTPException(422, str(llm_err))

        per_req_rag = SelfCorrectingRAG(
            llm=llm,
            vector_store=request.app.state.vector_store,
            confidence_threshold=get_settings().confidence_threshold,
            max_retries=get_settings().max_retries,
        )
        try:
            result = await run_in_threadpool(per_req_rag.answer, req.message, context_override, sources_override)
        except ValueError as user_err:
            # Friendly API errors raised by LLM adapters (rate limit, bad key, missing model, etc.)
            await db.rollback()
            raise HTTPException(422, str(user_err))

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

    except HTTPException:
        raise  # already formatted — don't re-wrap
    except Exception as e:
        await db.rollback()
        import traceback
        logger.error(f"Chat endpoint error: {e}\n{traceback.format_exc()}")
        raise HTTPException(500, "An unexpected server error occurred. Please try again.")


# Static model lists per provider (used as fallback or when live fetch isn't available)
_PROVIDER_MODELS: dict = {
    "groq": [
        {"id": "llama-3.1-8b-instant",    "label": "LLaMA 3.1 8B Instant (fast)"},
        {"id": "llama-3.1-70b-versatile", "label": "LLaMA 3.1 70B Versatile"},
        {"id": "llama3-8b-8192",          "label": "LLaMA 3 8B"},
        {"id": "llama3-70b-8192",         "label": "LLaMA 3 70B"},
        {"id": "gemma2-9b-it",            "label": "Gemma 2 9B"},
    ],
    "openai": [
        {"id": "gpt-4o",       "label": "GPT-4o"},
        {"id": "gpt-4o-mini",  "label": "GPT-4o Mini (fast)"},
        {"id": "gpt-4-turbo",  "label": "GPT-4 Turbo"},
        {"id": "o1-mini",      "label": "o1 Mini (reasoning)"},
    ],
    "gemini": [
        {"id": "gemini-2.0-flash",         "label": "Gemini 2.0 Flash"},
        {"id": "gemini-2.0-flash-lite",    "label": "Gemini 2.0 Flash Lite (fast)"},
        {"id": "gemini-1.5-pro-002",       "label": "Gemini 1.5 Pro 002 (1M context)"},
        {"id": "gemini-1.5-flash-002",     "label": "Gemini 1.5 Flash 002"},
        {"id": "gemini-1.5-flash-8b-001",  "label": "Gemini 1.5 Flash 8B (fast)"},
    ],
    "nvidia": [
        {"id": "meta/llama-3.1-8b-instruct",                   "label": "Meta Llama 3.1 8B"},
        {"id": "meta/llama-3.1-70b-instruct",                  "label": "Meta Llama 3.1 70B"},
        {"id": "meta/llama-3.3-70b-instruct",                  "label": "Meta Llama 3.3 70B"},
        {"id": "nvidia/llama-3.1-nemotron-70b-instruct",       "label": "NVIDIA Nemotron 70B"},
        {"id": "mistralai/mistral-7b-instruct-v0.3",           "label": "Mistral 7B"},
        {"id": "microsoft/phi-3-mini-128k-instruct",           "label": "Phi-3 Mini 128K"},
    ],
    "aws": [
        {"id": "anthropic.claude-3-5-sonnet-20241022-v2:0", "label": "Claude 3.5 Sonnet"},
        {"id": "anthropic.claude-3-haiku-20240307-v1:0",    "label": "Claude 3 Haiku (fast)"},
        {"id": "amazon.nova-lite-v1:0",                     "label": "Amazon Nova Lite"},
        {"id": "meta.llama3-8b-instruct-v1:0",              "label": "Llama 3 8B"},
        {"id": "meta.llama3-70b-instruct-v1:0",             "label": "Llama 3 70B"},
        {"id": "mistral.mistral-7b-instruct-v0:2",          "label": "Mistral 7B"},
    ],
}


@router.get("/models")
async def list_models(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_provider: Optional[str] = Header(None, alias="X-Provider"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    from fastapi.concurrency import run_in_threadpool
    repo = UserSettingRepository(UserSetting, db)
    settings = get_settings()

    # Resolve provider
    provider = x_provider
    if not provider:
        s = await repo.get_by_user_and_key(current_user.id, "active_provider")  # type: ignore[arg-type]
        provider = str(s.value).strip() if s and s.value else None
    provider = provider or "groq"

    async def _get_setting(key: str):
        s = await repo.get_by_user_and_key(current_user.id, key)  # type: ignore[arg-type]
        v = str(s.value).strip() if s and s.value else None
        return v or None

    if provider == "groq":
        api_key = x_api_key or await _get_setting("groq_api_key") or getattr(settings, "groq_api_key", None)
        if not api_key:
            return {"source": "fallback", "models": _PROVIDER_MODELS["groq"]}
        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=api_key)
            response = await client.models.list()
            models = [
                {"id": m.id, "label": _make_label(m.id)}
                for m in sorted(response.data, key=lambda m: m.id)
                if "whisper" not in m.id.lower()
            ]
            return {"source": "groq", "models": models or _PROVIDER_MODELS["groq"]}
        except Exception as exc:
            logger.warning(f"Could not fetch Groq model list: {exc}")
            return {"source": "fallback", "models": _PROVIDER_MODELS["groq"]}

    if provider == "openai":
        api_key = x_api_key or await _get_setting("openai_api_key") or getattr(settings, "openai_api_key", None)
        if not api_key:
            return {"source": "fallback", "models": _PROVIDER_MODELS["openai"]}
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key)
            response = await client.models.list()
            chat_ids = {"gpt", "o1", "o3"}
            models = [
                {"id": m.id, "label": m.id}
                for m in sorted(response.data, key=lambda m: m.id)
                if any(m.id.startswith(p) for p in chat_ids)
            ]
            return {"source": "openai", "models": models or _PROVIDER_MODELS["openai"]}
        except Exception as exc:
            logger.warning(f"Could not fetch OpenAI model list: {exc}")
            return {"source": "fallback", "models": _PROVIDER_MODELS["openai"]}

    if provider == "gemini":
        api_key = x_api_key or await _get_setting("gemini_api_key") or getattr(settings, "gemini_api_key", None)
        if not api_key:
            return {"source": "fallback", "models": _PROVIDER_MODELS["gemini"]}
        try:
            # Bare unversioned model IDs that the API still lists but can no longer serve
            _GEMINI_DEPRECATED = {
                "gemini-pro", "gemini-ultra", "gemini-nano",
                "gemini-1.0-pro", "gemini-1.0-pro-vision",
                "gemini-1.5-pro", "gemini-1.5-flash",
            }
            def _list_gemini():
                from google import genai
                client = genai.Client(api_key=api_key)
                result = []
                for m in client.models.list():
                    raw_name = m.name or ""
                    model_id = raw_name.removeprefix("models/")
                    if not model_id.startswith("gemini"):
                        continue  # skip embedding / vision-only models
                    if model_id in _GEMINI_DEPRECATED:
                        continue
                    # Accept models that support generateContent in either field name
                    methods = (
                        getattr(m, "supported_generation_methods", None)
                        or getattr(m, "supported_actions", None)
                        or []
                    )
                    if methods and "generateContent" not in methods:
                        continue
                    label = (m.display_name or model_id)
                    result.append({"id": model_id, "label": label})
                return sorted(result, key=lambda x: x["id"])
            models = await run_in_threadpool(_list_gemini)
            return {"source": "gemini", "models": models or _PROVIDER_MODELS["gemini"]}
        except Exception as exc:
            logger.warning(f"Could not fetch Gemini model list: {exc}")
            return {"source": "fallback", "models": _PROVIDER_MODELS["gemini"]}

    if provider == "nvidia":
        api_key = x_api_key or await _get_setting("nvidia_api_key") or getattr(settings, "nvidia_api_key", None)
        if not api_key:
            return {"source": "fallback", "models": _PROVIDER_MODELS["nvidia"]}
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url="https://integrate.api.nvidia.com/v1")
            response = await client.models.list()
            models = [
                {"id": m.id, "label": m.id}
                for m in sorted(response.data, key=lambda m: m.id)
            ]
            return {"source": "nvidia", "models": models or _PROVIDER_MODELS["nvidia"]}
        except Exception as exc:
            logger.warning(f"Could not fetch NVIDIA model list: {exc}")
            return {"source": "fallback", "models": _PROVIDER_MODELS["nvidia"]}

    if provider == "aws":
        access_key = await _get_setting("aws_access_key_id")
        secret_key = await _get_setting("aws_secret_access_key")
        region = await _get_setting("aws_region") or "us-east-1"
        if not access_key or not secret_key:
            return {"source": "fallback", "models": _PROVIDER_MODELS["aws"]}
        try:
            def _list_aws():
                import boto3
                client = boto3.client("bedrock",
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region)
                response = client.list_foundation_models(byOutputModality="TEXT")
                result = []
                for m in response.get("modelSummaries", []):
                    result.append({"id": m["modelId"], "label": m.get("modelName", m["modelId"])})
                return sorted(result, key=lambda x: x["id"])
            models = await run_in_threadpool(_list_aws)
            return {"source": "aws", "models": models or _PROVIDER_MODELS["aws"]}
        except Exception as exc:
            logger.warning(f"Could not fetch AWS Bedrock model list: {exc}")
            return {"source": "fallback", "models": _PROVIDER_MODELS["aws"]}

    return {"source": "fallback", "models": _PROVIDER_MODELS.get(provider, [])}


def _make_label(model_id: str) -> str:
    parts = model_id.split("-")
    return " — ".join([parts[0].capitalize()] + parts[1:]) if parts else model_id


@router.get("/llm-provider")
async def get_llm_provider(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from ..services.ollama_service import OllamaService

    repo = UserSettingRepository(UserSetting, db)
    settings = get_settings()

    async def _get(key: str):
        s = await repo.get_by_user_and_key(current_user.id, key)  # type: ignore[arg-type]
        return str(s.value).strip() if s and s.value else None

    active_provider = await _get("active_provider") or settings.active_provider or "groq"
    groq_key    = await _get("groq_api_key")    or settings.groq_api_key
    openai_key  = await _get("openai_api_key")  or settings.openai_api_key
    gemini_key  = await _get("gemini_api_key")  or settings.gemini_api_key
    nvidia_key  = await _get("nvidia_api_key")  or settings.nvidia_api_key
    aws_key     = await _get("aws_access_key_id") or settings.aws_access_key_id
    ollama_running = OllamaService.check_available(settings.ollama_base_url)

    has_creds = {
        "groq":   bool(groq_key),
        "openai": bool(openai_key),
        "gemini": bool(gemini_key),
        "nvidia": bool(nvidia_key),
        "aws":    bool(aws_key),
        "ollama": ollama_running,
    }
    display_provider = active_provider if has_creds.get(active_provider) else "none"

    return {
        "active_provider": display_provider,
        "ollama": {"available": ollama_running, "model": settings.ollama_model},
    }
