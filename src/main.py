from fastapi import FastAPI
# Force reload 2
from contextlib import asynccontextmanager

from .shared.config import get_settings
from .shared.logging import setup_logging
from .shared.middleware import setup_middleware
from .shared.exception_handler import setup_exception_handler
from .shared.cors import setup_cors
from .db.database import Database
from .api import auth_router, chat_router, kb_router, documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level)

    db = Database(settings.database_url)
    db.create_all()

    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="2.0",
        lifespan=lifespan
    )

    # Middleware
    setup_middleware(app)
    setup_exception_handler(app)
    setup_cors(app, settings.cors_origins)

    # Include routers
    app.include_router(auth_router)
    app.include_router(kb_router)
    app.include_router(documents_router)
    app.include_router(chat_router)

    # Settings endpoint
    from fastapi import Depends
    from sqlalchemy.orm import Session
    from .api.deps import get_db_session, get_current_user
    from .db.repositories import UserSettingRepository
    from .db.models import UserSetting, User

    @app.get("/settings")
    def get_settings_endpoint(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session)
    ):
        repo = UserSettingRepository(UserSetting, db)
        settings = repo.get_all_for_user(current_user.id)
        return {s.key: s.value for s in settings}

    @app.post("/settings")
    def update_settings(
        key: str,
        value: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db_session)
    ):
        repo = UserSettingRepository(UserSetting, db)
        repo.upsert(current_user.id, key, value)
        db.commit()
        return {"status": "updated", "key": key}

    # Health check
    @app.get("/health")
    @app.get("/ready")
    def health():
        return {"status": "ok", "version": "2.0"}

    @app.get("/debug-test")
    def debug_test():
        return {"debug": "ANTIGRAVITY_IS_HERE_V3"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)