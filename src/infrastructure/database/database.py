from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from .models import Base


class Database:
    def __init__(self, database_url: str):
        connect_args = {}
        if database_url.startswith("sqlite"):
            # Ensure directory exists for SQLite
            db_path = database_url.replace("sqlite:///", "")
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            connect_args["check_same_thread"] = False
            connect_args["timeout"] = 15

        from sqlalchemy.pool import NullPool
        self.engine = create_async_engine(
            database_url,
            connect_args=connect_args,
            poolclass=NullPool,
        )

        if database_url.startswith("sqlite"):
            from sqlalchemy import event
            @event.listens_for(self.engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                try:
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                except Exception:
                    pass
                cursor.close()
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, class_=AsyncSession)

    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        session = self.SessionLocal()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_database() -> Database:
    from ..shared.config import get_settings
    return Database(get_settings().db_url)
