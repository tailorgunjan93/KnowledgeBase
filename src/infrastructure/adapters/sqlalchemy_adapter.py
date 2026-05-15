"""Wrapper around SQLAlchemy. All ORM imports live here."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.logger import get_logger
from src.domain.models import Base, Document

log = get_logger(__name__)

class SQLAlchemyAdapter:
    """Implements DocumentStorePort using SQLAlchemy + SQLite (swappable)."""

    def __init__(self, db_url: str) -> None:
        log.info(f"Initializing Async SQLAlchemy DB: {db_url}")
        from sqlalchemy.pool import NullPool

        if db_url.startswith("sqlite"):
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            connect_args = {"check_same_thread": False, "timeout": 15}
        else:
            connect_args = {}

        self.engine = create_async_engine(db_url, connect_args=connect_args, poolclass=NullPool)

        if db_url.startswith("sqlite+aiosqlite"):
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

        self._Session = sessionmaker(bind=self.engine, class_=AsyncSession)

    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _session(self) -> AsyncSession:
        return self._Session()

    async def save_document(self, doc: dict) -> str:
        async with self._session() as s:
            record = Document(**doc)
            s.add(record)
            await s.commit()
            return str(record.id)

    async def get_document(self, doc_id: str) -> dict | None:
        async with self._session() as s:
            record = await s.get(Document, doc_id)
            if record:
                data = {c.name: getattr(record, c.name) for c in record.__table__.columns}
                return data
            return None

    async def list_documents(self, kb_id: str) -> list[dict]:
        from sqlalchemy import select
        async with self._session() as s:
            records = (await s.scalars(select(Document).filter_by(kb_id=kb_id))).all()
            return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]
