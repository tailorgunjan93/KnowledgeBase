from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sys
import traceback

from .core.settings import get_settings
from .core.logger import get_logger
from .core.exceptions import KnowledgeBaseError
from .shared.middleware import setup_middleware
from .shared.exception_handler import setup_exception_handler
from .shared.cors import setup_cors

# Infrastructure Adapters
from .infrastructure.adapters.groq_llm_adapter import GroqLLMAdapter
from .infrastructure.adapters.faiss_adapter import FAISSAdapter
from .infrastructure.adapters.sentence_transformer_embedder import SentenceTransformerEmbedder
from .infrastructure.adapters.sqlalchemy_adapter import SQLAlchemyAdapter

# Application Services
from .application.rag_service import SelfCorrectingRAG

log = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    log.info(f"Starting {settings.app_name}...")

    # Initialize DB adapter
    db_adapter = SQLAlchemyAdapter(settings.db_url)
    
    # Cleanup stuck documents (legacy logic integration)
    from .api.documents import cleanup_stuck_documents
    with db_adapter._Session() as session:
        cleanup_stuck_documents(session)

    yield

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="3.0",
        lifespan=lifespan
    )

    # Middleware & Global Exception Handlers
    setup_middleware(app)
    setup_exception_handler(app)
    setup_cors(app, settings.cors_origins)

    # Task 1.6 — Register KnowledgeBaseError exception handlers
    @app.exception_handler(KnowledgeBaseError)
    async def kb_exception_handler(request: Request, exc: KnowledgeBaseError):
        return JSONResponse(status_code=400, content={"error": str(exc)})

    # Composition Root
    embedder = SentenceTransformerEmbedder(settings.embedder_model)
    vector_store = FAISSAdapter(embedder)
    llm = GroqLLMAdapter(settings)
    rag_service = SelfCorrectingRAG(llm=llm, vector_store=vector_store)
    
    # Store in app state for access in routes if needed
    app.state.rag_service = rag_service

    # Include routers
    from .api import auth_router, chat_router, kb_router, documents_router
    app.include_router(auth_router)
    app.include_router(kb_router)
    app.include_router(documents_router)
    app.include_router(chat_router)

    # Health check
    @app.get("/health")
    @app.get("/ready")
    def health():
        return {"status": "ok", "version": "3.0"}

    # Global exception logger for ANY unhandled error
    @app.middleware("http")
    async def log_exceptions(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            print("\n=== UNHANDLED EXCEPTION ===", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            print("=== END ===\n", file=sys.stderr)
            sys.stderr.flush()
            raise

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)