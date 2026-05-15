import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.search.web_search import WebSearchEngine
from ..core.settings import get_settings
from ..domain.models import ChatSession, Message, User, UserSetting
from ..infrastructure.database.repositories import (
    ChatSessionRepository,
    MessageRepository,
    UserSettingRepository,
)
from .deps import get_current_user, get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


class CreateSessionRequest(BaseModel):
    kb_id: int | None = None
    title: str | None = "New Chat"


class SessionResponse(BaseModel):
    id: int
    kb_id: int | None
    title: str
    created_at: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    intent: str | None = None
    confidence: str | None = None
    sources: list[dict] | None = None


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None
    kb_id: int | None = None # Legacy support
    kb_ids: list[int] | None = None
    enable_web_search: bool = False
    advanced_rag: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: int
    intent: str | None = None
    confidence: str | None = None
    sources: list[dict] | None = None


@router.get("/sessions", response_model=list[SessionResponse])
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
        from ..shared.rbac import require_kb_role
        await require_kb_role(req.kb_id, "viewer", current_user, db)

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


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
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


@router.post("/chat")
async def chat(
    request: Request,
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    from .deps import get_database
    db_manager = get_database()

    import json

    from fastapi.responses import StreamingResponse

    async def stream_generator():
        # Open the session INSIDE the generator to ensure it lives as long as the stream
        async with db_manager.session() as db:
            try:
                # 1. Session Setup
                session_repo = ChatSessionRepository(ChatSession, db)
                if req.session_id:
                    session = await session_repo.get_by_user_and_id(req.session_id, current_user.id)
                    if not session:
                        yield json.dumps({"type": "error", "content": "Session not found"}) + "\n"
                        return
                else:
                    from datetime import datetime as _dt
                    _ts = _dt.now().strftime("%b %d %H:%M")
                    _short_msg = req.message[:40] + "..." if len(req.message) > 40 else req.message
                    session = await session_repo.create(
                        user_id=current_user.id,
                        kb_id=req.kb_ids[0] if req.kb_ids and len(req.kb_ids) > 0 else req.kb_id,
                        title=f"[{_ts}] {_short_msg}"
                    )
                    await db.flush()

                session_id = session.id

                # Save user message immediately
                msg_repo = MessageRepository(Message, db)
                await msg_repo.create(
                    session_id=session_id,
                    role="user",
                    content=req.message
                )
                await db.commit()

                # Yield session ID early so UI can update
                yield json.dumps({"type": "session", "session_id": session_id}) + "\n"

                context_override = None
                sources_override = None

                kb_id = req.kb_ids[0] if req.kb_ids and len(req.kb_ids) > 0 else req.kb_id

                # Verify KB access if a KB is being used
                if kb_id:
                    from ..shared.rbac import require_kb_role as _require_kb_role
                    try:
                        await _require_kb_role(kb_id, "viewer", current_user, db)
                    except Exception:
                        yield json.dumps({"type": "error", "content": "Access denied to this knowledge base"}) + "\n"
                        return

                from fastapi.concurrency import run_in_threadpool

                # 2. KB Retrieval
                if kb_id:
                    from ..domain.models import Document
                    from ..infrastructure.database.repositories import DocumentRepository
                    doc_repo = DocumentRepository(Document, db)
                    docs = await doc_repo.get_by_kb(kb_id)
                    if docs:
                        yield json.dumps({"type": "status", "content": "🔍 Searching knowledge base..."}) + "\n"
                        from ..core.search.dynamic_index import IndexManager
                        index_manager = IndexManager(kb_id)
                        doc_ids = [d.id for d in docs if d.indexed]

                        if doc_ids:
                            # Advanced RAG logic
                            hyde_query = None
                            expanded_queries = None

                            if req.advanced_rag:
                                from ..core.search.query_processor import QueryProcessor
                                from ..infrastructure.adapters.llm_provider_factory import (
                                    get_llm_for_user,
                                )

                                yield json.dumps({"type": "status", "content": "🧠 Optimizing search query..."}) + "\n"
                                llm_for_proc = await get_llm_for_user(current_user.id, db)
                                processor = QueryProcessor(llm_for_proc)

                                # Parallelize HyDE and Expansion
                                import asyncio
                                hyde_task = asyncio.create_task(processor.generate_hypothetical_document(req.message))
                                expansion_task = asyncio.create_task(processor.expand_query(req.message))

                                hyde_query, expanded_queries = await asyncio.gather(hyde_task, expansion_task)
                                yield json.dumps({"type": "status", "content": "🎯 Retrieving precision sources..."}) + "\n"

                            # Create a map for titles since the index only has IDs
                            doc_titles = {str(d.id): d.title for d in docs}

                            results = await run_in_threadpool(
                                index_manager.search_kb,
                                req.message,
                                doc_ids,
                                5,
                                hyde_query=hyde_query,
                                expanded_queries=expanded_queries
                            )
                            if results:
                                context_override = "[KNOWLEDGE BASE CONTEXT]\n" + "\n\n".join([r.get('text', '') for r in results])
                                # Deduplicate by doc_id — keep best chunk per document.
                                # Use faiss_score (0-1 normalized) as the relevance indicator;
                                # fall back to combined_score for BM25-only hits.
                                seen_docs: dict = {}
                                for r in results:
                                    did = str(r.get("doc_id"))
                                    # faiss_score is 1/(1+dist) → already in [0,1]; best for % display
                                    r_score = r.get("faiss_score") or r.get("combined_score") or 0.0
                                    if did not in seen_docs or r_score > seen_docs[did]["score"]:
                                        seen_docs[did] = {
                                            "type": "kb",
                                            "title": doc_titles.get(did) or "Untitled",
                                            "text": r.get("text", ""),
                                            "doc_id": did,
                                            "id": did,
                                            "score": r_score if r_score > 0 else None,
                                            "metadata": r.get("metadata"),
                                        }
                                sources_override = list(seen_docs.values())

                # 3. Web Search
                if req.enable_web_search:
                    yield json.dumps({"type": "status", "content": "🌐 Searching the web..."}) + "\n"
                    try:
                        from ..shared.encryption import decrypt
                        settings_repo = UserSettingRepository(UserSetting, db)
                        serper_key_setting = await settings_repo.get_by_user_and_key(current_user.id, "serper_api_key")
                        raw_serper_key = serper_key_setting.value if serper_key_setting else None
                        # Decrypt if stored encrypted (enc:... prefix); pass-through for plaintext
                        final_serper_key = decrypt(raw_serper_key) if raw_serper_key else get_settings().serper_api_key

                        def _run_web_search_with_key(key):
                            combined = []
                            try:
                                engine = WebSearchEngine(serper_api_key=key)
                                results = engine.search(req.message)
                                if results:
                                    combined = results
                            except Exception:  # noqa: BLE001
                                pass
                            return combined

                        web_results = await run_in_threadpool(_run_web_search_with_key, final_serper_key)
                        if web_results:
                            web_context = "[WEB SEARCH RESULTS]\n" + "\n\n".join([f"Title: {r.get('title')}\nURL: {r.get('href')}\n{r.get('body')}" for r in web_results])
                            context_override = (context_override + "\n\n" + web_context) if context_override else web_context
                            web_sources = [{"type": "web", "title": r.get("title"), "url": r.get("href"), "text": r.get("body")} for r in web_results]
                            sources_override = (sources_override or []) + web_sources
                    except Exception as e:
                        logger.warning(f"Web search failed in stream: {e}")

                # 4. LLM Stream
                yield json.dumps({"type": "status", "content": "Synthesizing answer..."}) + "\n"
                from ..application.rag_service import SelfCorrectingRAG
                from ..infrastructure.adapters.llm_provider_factory import get_llm_for_user

                llm = await get_llm_for_user(current_user.id, db)
                per_req_rag = SelfCorrectingRAG(llm=llm, vector_store=request.app.state.vector_store)

                stream, sources = per_req_rag.answer_stream(req.message, context_override, sources_override)

                full_content = ""
                for chunk in stream:
                    full_content += chunk
                    yield json.dumps({"type": "content", "delta": chunk}) + "\n"

                # 5. Final Save
                from ..infrastructure.database.repositories import MessageRepository as GenMsgRepo
                msg_repo_gen = GenMsgRepo(Message, db)
                await msg_repo_gen.create(session_id=session_id, role="assistant", content=full_content, confidence="0.9", sources=sources)
                await db.commit()

                yield json.dumps({"type": "meta", "session_id": session_id, "sources": sources}) + "\n"

            except Exception as e:
                await db.rollback()
                import traceback
                logger.error(f"Stream error: {e}\n{traceback.format_exc()}")
                yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")


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
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    x_provider: str | None = Header(None, alias="X-Provider"),
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
            _gemini_deprecated = {
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
                    if model_id in _gemini_deprecated:
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
