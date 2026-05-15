from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from pydantic import BaseModel
import shutil
import uuid
from pathlib import Path

try:
    from .deps import get_db_session, get_current_user
    from ..infrastructure.database.repositories import DocumentRepository, KnowledgeBaseRepository
    from ..domain.models import Document, User, KnowledgeBase
    from ..shared.exceptions import NotFoundError, ValidationError
except (ImportError, ModuleNotFoundError):
    try:
        from src.api.deps import get_db_session, get_current_user
        from src.infrastructure.database.repositories import DocumentRepository, KnowledgeBaseRepository
        from src.domain.models import Document, User, KnowledgeBase
        from src.shared.exceptions import NotFoundError, ValidationError
    except (ImportError, ModuleNotFoundError):
        from api.deps import get_db_session, get_current_user
        from db.repositories import DocumentRepository, KnowledgeBaseRepository
        from db.models import Document, User, KnowledgeBase
        from shared.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/api", tags=["documents"])


class DocumentResponse(BaseModel):
    id: int
    kb_id: int
    title: str
    file_type: Optional[str] = None
    chunk_count: int
    indexed: bool
    index_status: str


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int


class SummarizeRequest(BaseModel):
    text: str
    max_length: Optional[int] = 500


class SummarizeResponse(BaseModel):
    summary: str
    original_length: int
    summary_length: int
    key_points: Optional[List[str]] = None


@router.get("/kb/{kb_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100
):
    from ..shared.rbac import require_kb_role
    await require_kb_role(kb_id, "viewer", current_user, db)

    repo = DocumentRepository(Document, db)
    docs = await repo.get_by_kb(kb_id, skip=skip, limit=limit)

    return DocumentListResponse(
        items=[
            DocumentResponse(
                id=d.id,
                kb_id=d.kb_id,
                title=d.title or "Untitled",
                file_type=d.file_type,
                chunk_count=d.chunk_count,
                indexed=d.indexed,
                index_status=d.index_status
            )
            for d in docs
        ],
        total=len(docs)
    )


import concurrent.futures

@router.post("/kb/{kb_id}/documents")
async def upload_document(
    kb_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        from ..shared.rbac import require_kb_role
        try:
            await require_kb_role(kb_id, "editor", current_user, db)
        except Exception:
            return {"detail": "Insufficient access to this knowledge base", "status": "error"}

        try:
            file_bytes = await file.read()
        except Exception as read_err:
            return {"detail": f"Failed to read uploaded file: {read_err}", "status": "error"}

        upload_dir = Path(f"data_storage/uploads/{kb_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        with file_path.open("wb") as f:
            f.write(file_bytes)

        doc_repo = DocumentRepository(Document, db)
        try:
            doc = await doc_repo.create(
                kb_id=kb_id,
                user_id=current_user.id,
                title=file.filename,
                content="",
                file_type=file.filename.split(".")[-1].lower() if "." in file.filename else "unknown",
                file_path=str(file_path),
                index_status="processing"
            )
            doc_id = doc.id
            await db.commit()
        except Exception as db_err:
            await db.rollback()
            raise ValidationError(f"Database error: {str(db_err)}")

        from ..core.settings import get_settings
        settings = get_settings()
        db_url = settings.db_url

        if settings.celery_broker_url:
            # ── Celery path: persistent queue, survives restarts ──────────
            from src.worker.tasks.indexing import index_document
            index_document.delay(doc_id, kb_id, str(file_path), file.filename, db_url)
        else:
            # ── Fallback path: FastAPI BackgroundTasks (no Redis needed) ──
            background_tasks.add_task(_process_document_task, doc_id, kb_id, str(file_path), file.filename, db_url)

        return {
            "id": doc_id,
            "title": file.filename,
            "status": "uploaded",
            "index_status": "processing"
        }
    except Exception as e:
        import traceback
        error_msg = f"UPLOAD FAILED: {str(e)} - {traceback.format_exc()}"
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"detail": error_msg, "debug": True})


async def _process_document_task(doc_id: int, kb_id: int, file_path_str: str, filename: str, db_url: str):
    """Background task: extract text, then index document, then update DB status."""
    from ..infrastructure.database.database import Database
    from ..core.search.dynamic_index import IndexManager

    file_path = Path(file_path_str)
    
    try:
        from fastapi.concurrency import run_in_threadpool
        print(f"BG_TASK: Starting extraction for doc {doc_id} ({filename})...")
        extraction_result = await run_in_threadpool(_extract_file_content_sync, file_path, filename)
        content = extraction_result["text"]
        pages = extraction_result["pages"]
        
        if content.startswith("Error"):
            print(f"BG_TASK ERROR: Extraction failed for doc {doc_id}: {content}")
            raise Exception(content)
        
        print(f"BG_TASK: Extraction complete for doc {doc_id}. Length: {len(content)} chars, {len(pages)} pages.")

        bg_db = Database(db_url)
        async with bg_db.session() as session:
            doc_obj = await session.get(Document, doc_id)
            if doc_obj:
                doc_obj.content = content
            await session.commit()

        print(f"BG_TASK: Starting indexing for doc {doc_id}...")
        index_mgr = IndexManager(kb_id)
        success = await run_in_threadpool(index_mgr.create_document_index, doc_id, content, pages)
        print(f"BG_TASK: Indexing {'successful' if success else 'failed'} for doc {doc_id}.")

        async with bg_db.session() as session:
            doc_obj = await session.get(Document, doc_id)
            if doc_obj:
                doc_obj.indexed = success
                doc_obj.index_status = "indexed" if success else "failed"
                chunk_count = len(content.split()) // 250 if content else 0
                doc_obj.chunk_count = max(chunk_count, 1) if success else 0
            await session.commit()
            
    except Exception as e:
        print(f"DEBUG background processing error for doc {doc_id}: {e}")
        try:
            bg_db = Database(db_url)
            async with bg_db.session() as session:
                doc_obj = await session.get(Document, doc_id)
                if doc_obj:
                    doc_obj.indexed = False
                    doc_obj.index_status = "failed"
                await session.commit()
        except Exception:
            pass


def _extract_file_content_sync(file_path: Path, filename: str) -> dict:
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    pages = []
    full_text = ""

    try:
        if ext == "txt":
            full_text = file_path.read_text(encoding="utf-8")
            pages = [{"page": 1, "text": full_text}]
        elif ext == "pdf":
            try:
                import PyPDF2
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for i, page in enumerate(reader.pages):
                        p_text = page.extract_text() or ""
                        pages.append({"page": i + 1, "text": p_text})
                full_text = "\n".join(p["text"] for p in pages)
            except Exception:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        p_text = page.extract_text() or ""
                        pages.append({"page": i + 1, "text": p_text})
                full_text = "\n".join(p["text"] for p in pages)
        elif ext in ["doc", "docx"]:
            from docx import Document as DocxDocument
            docx = DocxDocument(file_path)
            full_text = "\n".join(para.text for para in docx.paragraphs)
            pages = [{"page": 1, "text": full_text}]
        elif ext in ["xlsx", "xls"]:
            import pandas as pd
            df = pd.read_excel(file_path)
            full_text = df.to_string()
            pages = [{"page": 1, "text": full_text}]
        else:
            full_text = file_path.read_text(encoding="utf-8", errors="ignore")
            pages = [{"page": 1, "text": full_text}]
        
        return {"text": full_text, "pages": pages}
    except Exception as e:
        err = f"Error extracting content: {str(e)}"
        return {"text": err, "pages": [{"page": 1, "text": err}]}


async def extract_file_content(file_path: Path, filename: str) -> str:
    res = _extract_file_content_sync(file_path, filename)
    return res["text"]


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from ..shared.rbac import require_kb_role
    repo = DocumentRepository(Document, db)
    doc = await repo.get_by_id(doc_id)

    if not doc:
        raise NotFoundError("Document not found")

    # Require editor+ on the KB (admins bypass)
    await require_kb_role(doc.kb_id, "editor", current_user, db)

    index_path = Path(f"data_storage/indices/{doc_id}")
    if index_path.exists():
        shutil.rmtree(index_path)

    if doc.file_path:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()

    await repo.delete(doc_id)
    await db.commit()

    return {"status": "deleted", "id": doc_id}
 
@router.get("/documents/{doc_id}/file")
async def get_document_file(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from ..shared.rbac import require_kb_role
    repo = DocumentRepository(Document, db)
    doc = await repo.get_by_id(doc_id)

    if not doc:
        raise NotFoundError("Document not found")

    await require_kb_role(doc.kb_id, "viewer", current_user, db)
 
    if not doc.file_path:
        raise NotFoundError("File not found on disk")
 
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise NotFoundError("File not found on disk")
 
    return FileResponse(
        path=file_path,
        filename=doc.title or f"document_{doc_id}",
        media_type="application/pdf" if doc.file_type == "pdf" else None
    )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    req: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from ..core.services.summarizer import Summarizer
    from ..infrastructure.adapters.llm_provider_factory import get_llm_for_user
    from fastapi.concurrency import run_in_threadpool

    try:
        llm = await get_llm_for_user(current_user.id, db)  # type: ignore[arg-type]
    except ValueError as e:
        raise HTTPException(422, str(e))

    summarizer = Summarizer()
    result = await run_in_threadpool(
        summarizer.summarize_text_with_llm, req.text, llm, req.max_length or 500
    )

    if "error" in result:
        raise ValidationError(result["error"])

    return SummarizeResponse(
        summary=result["summary"],
        original_length=result["original_length"],
        summary_length=result["summary_length"],
        key_points=result.get("key_points")
    )

async def cleanup_stuck_documents(db: AsyncSession):
    from ..domain.models import Document
    from sqlalchemy import update
    # Bulk update all stuck documents to 'failed' status
    await db.execute(
        update(Document)
        .where(Document.index_status == "processing")
        .values(index_status="failed")
    )
    await db.commit()

@router.post("/summarize/file", response_model=SummarizeResponse)
async def summarize_file(
    file: UploadFile = File(...),
    max_length: int = Form(500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    from ..core.services.summarizer import Summarizer
    from ..infrastructure.adapters.llm_provider_factory import get_llm_for_user
    from fastapi.concurrency import run_in_threadpool

    try:
        llm = await get_llm_for_user(current_user.id, db)  # type: ignore[arg-type]
    except ValueError as e:
        raise HTTPException(422, str(e))

    upload_dir = Path(f"data_storage/uploads/temp_{current_user.id}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"

    with file_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    content = await extract_file_content(file_path, file.filename)
    if content.startswith("Error"):
        if file_path.exists():
            file_path.unlink()
        raise ValidationError(content)

    if file_path.exists():
        file_path.unlink()

    summarizer = Summarizer()
    result = await run_in_threadpool(
        summarizer.summarize_text_with_llm, content, llm, max_length
    )
    
    if "error" in result:
        raise ValidationError(result["error"])

    return SummarizeResponse(
        summary=result["summary"],
        original_length=result["original_length"],
        summary_length=result["summary_length"],
        key_points=result.get("key_points")
    )