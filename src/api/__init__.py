from .auth import router as auth_router
from .chat import router as chat_router
from .knowledge_base import router as kb_router
from .documents import router as documents_router
from .admin import router as admin_router

__all__ = ["auth_router", "chat_router", "kb_router", "documents_router", "admin_router"]
