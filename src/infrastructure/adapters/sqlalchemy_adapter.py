"""Wrapper around SQLAlchemy. All ORM imports live here."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.domain.models import Base, Document, KnowledgeBase
from src.ports.document_store_port import DocumentStorePort
from src.core.logger import get_logger

log = get_logger(__name__)

class SQLAlchemyAdapter:
    """Implements DocumentStorePort using SQLAlchemy + SQLite (swappable)."""

    def __init__(self, db_url: str) -> None:
        log.info(f"Initializing SQLAlchemy DB: {db_url}")
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        self._Session = sessionmaker(bind=engine)

    def _session(self) -> Session:
        return self._Session()

    def save_document(self, doc: dict) -> str:
        with self._session() as s:
            record = Document(**doc)
            s.add(record)
            s.commit()
            return str(record.id)

    def get_document(self, doc_id: str) -> dict | None:
        with self._session() as s:
            record = s.get(Document, doc_id)
            if record:
                # Convert to dict, excluding internal state
                data = {c.name: getattr(record, c.name) for c in record.__table__.columns}
                return data
            return None

    def list_documents(self, kb_id: str) -> list[dict]:
        with self._session() as s:
            records = s.query(Document).filter_by(kb_id=kb_id).all()
            return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]
