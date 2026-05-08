from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from .deps import get_db_session, get_current_user, get_user_settings
from ..db.repositories import ChatSessionRepository, MessageRepository, UserSettingRepository, KnowledgeBaseRepository
from ..db.models import ChatSession, Message, User, UserSetting, KnowledgeBase
from ..services.llm_factory import LLMFactory
try:
    from ..services.web_search_service import WebSearchService
except (ImportError, ModuleNotFoundError):
    try:
        from src.services.web_search_service import WebSearchService
    except (ImportError, ModuleNotFoundError):
        from services.web_search_service import WebSearchService

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
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    skip: int = 0,
    limit: int = 20
):
    repo = ChatSessionRepository(ChatSession, db)
    sessions = repo.get_by_user(current_user.id, skip=skip, limit=limit)

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
def create_session(
    req: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    repo = ChatSessionRepository(ChatSession, db)

    # Validate kb_id if provided
    if req.kb_id:
        kb_repo = KnowledgeBaseRepository(KnowledgeBase, db)
        if not kb_repo.get_by_user_and_id(req.kb_id, current_user.id):
            raise HTTPException(404, "Knowledge base not found")

    session = repo.create(
        user_id=current_user.id,
        kb_id=req.kb_id,
        title=req.title
    )
    db.commit()

    return SessionResponse(
        id=session.id,
        kb_id=session.kb_id,
        title=session.title or "New Chat",
        created_at=session.created_at.isoformat()
    )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    repo = ChatSessionRepository(ChatSession, db)
    session = repo.get_by_user_and_id(session_id, current_user.id)

    if not session:
        raise HTTPException(404, "Session not found")

    msg_repo = MessageRepository(Message, db)
    messages = msg_repo.get_by_session(session_id)

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
def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from ..core.langgraph.nodes import RAGOrchestrator

    # Get API key (user-level or system-level)
    settings_repo = UserSettingRepository(UserSetting, db)
    api_key_setting = settings_repo.get_by_user_and_key(current_user.id, "groq_api_key")
    api_key = api_key_setting.value if api_key_setting else None

    if not api_key:
        from ..shared.config import get_settings
        api_key = get_settings().groq_api_key

    # Use LLM Factory — auto-detects Groq or Ollama
    try:
        llm_service = LLMFactory.create(api_key=api_key)
    except Exception as factory_err:
        raise HTTPException(
            400,
            "No LLM provider available. Either add a GROQ API key in Settings "
            "or install Ollama (https://ollama.com) for free local LLM."
        )

    # Get or create session
    session_repo = ChatSessionRepository(ChatSession, db)
    if req.session_id:
        session = session_repo.get_by_user_and_id(req.session_id, current_user.id)
        if not session:
            raise HTTPException(404, "Session not found")
    else:
        session = session_repo.create(
            user_id=current_user.id,
            kb_id=req.kb_ids[0] if req.kb_ids and len(req.kb_ids) > 0 else req.kb_id,
            title=req.message[:50] + "..." if len(req.message) > 50 else req.message
        )
        db.flush()

    # Save user message
    msg_repo = MessageRepository(Message, db)
    user_msg = msg_repo.create(
        session_id=session.id,
        role="user",
        content=req.message
    )
    db.flush()

    # Perform RAG chat
    try:
        orchestrator = RAGOrchestrator(llm_service)

        context = {}
        
        # Support both kb_id (legacy) and kb_ids (new)
        kb_ids_to_search = []
        if req.kb_ids:
            kb_ids_to_search.extend(req.kb_ids)
        elif req.kb_id:
            kb_ids_to_search.append(req.kb_id)
            
        if kb_ids_to_search:
            kb_repo = KnowledgeBaseRepository(KnowledgeBase, db)
            valid_kbs = []
            for k_id in kb_ids_to_search:
                if kb_repo.get_by_user_and_id(k_id, current_user.id):
                    valid_kbs.append(k_id)
            if valid_kbs:
                context["kb_ids"] = valid_kbs

        if req.enable_web_search:
            web_search = WebSearchService()
            search_results = web_search.search(req.message, max_results=3)
            context["web_results"] = [
                {"title": r.title, "body": r.body, "href": r.href}
                for r in search_results
            ]

        result = orchestrator.chat(req.message, context=context)

        # Save assistant message
        assistant_msg = msg_repo.create(
            session_id=session.id,
            role="assistant",
            content=result.get("response", ""),
            intent=result.get("intent"),
            confidence=result.get("confidence"),
            sources=result.get("sources")
        )
        db.commit()

        return ChatResponse(
            response=result.get("response", ""),
            session_id=session.id,
            intent=result.get("intent"),
            confidence=result.get("confidence"),
            sources=result.get("sources")
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Chat error: {str(e)}")