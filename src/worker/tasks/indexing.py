"""
Celery task: index_document
===========================
Ports the logic from ``src/api/documents._process_document_task`` into a
persistent Celery task that runs in a **separate worker process**.

Key differences from the FastAPI BackgroundTasks version:
- Runs synchronously (Celery workers are not async by default).
- Uses a plain synchronous SQLAlchemy session instead of aiosqlite.
- Retries up to 2 times (30-second back-off) before marking as failed.
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.worker.celery_app import celery_app

log = logging.getLogger(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _sync_session(db_url: str) -> Session:
    """Return a plain (synchronous) SQLAlchemy session.

    The ``db_url`` stored in settings is the raw URL without the async driver
    prefix (e.g. ``sqlite:///data_storage/knowledge_base.db``).  If someone
    passes a URL that already contains ``+aiosqlite`` we strip it so the sync
    engine can connect.
    """
    sync_url = db_url.replace("+aiosqlite", "")
    engine = create_engine(sync_url, connect_args={"check_same_thread": False})
    return Session(engine)


def _set_status(db_url: str, doc_id: int, **fields) -> None:
    """Update arbitrary Document fields synchronously."""
    from src.domain.models import Document  # local import keeps import graph clean

    session = _sync_session(db_url)
    try:
        doc = session.get(Document, doc_id)
        if doc:
            for key, value in fields.items():
                setattr(doc, key, value)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── task ──────────────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="worker.tasks.indexing.index_document",
    max_retries=2,
    default_retry_delay=30,   # seconds between retries
    acks_late=True,
)
def index_document(
    self,
    doc_id: int,
    kb_id: int,
    file_path_str: str,
    filename: str,
    db_url: str,
) -> dict:
    """
    Full document processing pipeline:
      1. Extract text from file (PDF / DOCX / XLSX / TXT …)
      2. Persist extracted content to the database
      3. Build FAISS + BM25 index
      4. Mark document as ``indexed`` (or ``failed`` on error)

    Returns a summary dict for the Celery result backend.
    """
    log.info("CELERY index_document START  doc_id=%s  file=%s", doc_id, filename)

    file_path = Path(file_path_str)

    # ------------------------------------------------------------------
    # Phase 1 – Text extraction (synchronous, same logic as original)
    # ------------------------------------------------------------------
    try:
        from src.api.documents import _extract_file_content_sync  # reuse existing fn

        extraction = _extract_file_content_sync(file_path, filename)
        content: str = extraction["text"]
        pages: list = extraction["pages"]

        if content.startswith("Error"):
            raise RuntimeError(f"Extraction failed: {content}")

        log.info(
            "CELERY index_document EXTRACTED  doc_id=%s  chars=%s  pages=%s",
            doc_id, len(content), len(pages),
        )
    except Exception as exc:
        log.exception("CELERY index_document EXTRACT_FAIL  doc_id=%s", doc_id)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            _set_status(db_url, doc_id, indexed=False, index_status="failed", chunk_count=0)
            return {"status": "failed", "doc_id": doc_id, "reason": str(exc)}

    # ------------------------------------------------------------------
    # Phase 2 – Persist extracted content
    # ------------------------------------------------------------------
    try:
        _set_status(db_url, doc_id, content=content)
    except Exception as exc:
        log.warning("CELERY index_document CONTENT_SAVE_FAIL  doc_id=%s  err=%s", doc_id, exc)
        # Non-fatal — continue to indexing even if content save fails

    # ------------------------------------------------------------------
    # Phase 3 – Build FAISS + BM25 index
    # ------------------------------------------------------------------
    try:
        from src.core.search.dynamic_index import IndexManager  # reuse existing fn

        index_mgr = IndexManager(kb_id)
        success: bool = index_mgr.create_document_index(doc_id, content, pages)

        log.info(
            "CELERY index_document INDEX_%s  doc_id=%s",
            "OK" if success else "FAIL", doc_id,
        )
    except Exception as exc:
        log.exception("CELERY index_document INDEX_EXCEPTION  doc_id=%s", doc_id)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            _set_status(db_url, doc_id, indexed=False, index_status="failed", chunk_count=0)
            return {"status": "failed", "doc_id": doc_id, "reason": str(exc)}

    # ------------------------------------------------------------------
    # Phase 4 – Finalise status
    # ------------------------------------------------------------------
    chunk_count = max(len(content.split()) // 250, 1) if success and content else 0
    _set_status(
        db_url,
        doc_id,
        indexed=success,
        index_status="indexed" if success else "failed",
        chunk_count=chunk_count if success else 0,
    )

    result_status = "indexed" if success else "failed"
    log.info("CELERY index_document DONE  doc_id=%s  status=%s", doc_id, result_status)
    return {"status": result_status, "doc_id": doc_id, "chunk_count": chunk_count}
