from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import shutil
import uuid
from pathlib import Path

try:
    from .deps import get_db_session, get_current_user
    from ..infrastructure.database.repositories import DocumentRepository, KnowledgeBaseRepository, UserSettingRepository
    from ..domain.models import Document, User, UserSetting, KnowledgeBase
    from ..shared.exceptions import NotFoundError, ValidationError
except (ImportError, ModuleNotFoundError):
    try:
        from src.api.deps import get_db_session, get_current_user
        from src.infrastructure.database.repositories import DocumentRepository, KnowledgeBaseRepository, UserSettingRepository
        from src.domain.models import Document, User, UserSetting, KnowledgeBase
        from src.shared.exceptions import NotFoundError, ValidationError
    except (ImportError, ModuleNotFoundError):
        # Fallback if src is root
        from api.deps import get_db_session, get_current_user
        from db.repositories import DocumentRepository, KnowledgeBaseRepository, UserSettingRepository
        from db.models import Document, User, UserSetting, KnowledgeBase
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


@router.get("/kb/{kb_id}/documents", response_model=DocumentListResponse)
def list_documents(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    skip: int = 0,
    limit: int = 100
):
    kb_repo = KnowledgeBaseRepository(KnowledgeBase, db)
    if not kb_repo.get_by_user_and_id(kb_id, current_user.id):
        raise NotFoundError("Knowledge base not found")

    repo = DocumentRepository(Document, db)
    docs = repo.get_by_kb(kb_id, skip=skip, limit=limit)

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
    db: Session = Depends(get_db_session)
):
    try:
        kb_repo = KnowledgeBaseRepository(KnowledgeBase, db)
        if not kb_repo.get_by_user_and_id(kb_id, current_user.id):
            return {"detail": "Knowledge base not found", "status": "error"}

        # Read all bytes before the file stream is consumed
        try:
            file_bytes = await file.read()
        except Exception as read_err:
            return {"detail": f"Failed to read uploaded file: {read_err}", "status": "error"}

        # Save uploaded file
        upload_dir = Path(f"data_storage/uploads/{kb_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        with file_path.open("wb") as f:
            f.write(file_bytes)

        # Create doc record immediately with 'processing' status
        doc_repo = DocumentRepository(Document, db)
        try:
            doc = doc_repo.create(
                kb_id=kb_id,
                user_id=current_user.id,
                title=file.filename,
                content="", # Will be filled in background
                file_type=file.filename.split(".")[-1].lower() if "." in file.filename else "unknown",
                file_path=str(file_path),
                index_status="processing"
            )
            db.commit()
            doc_id = doc.id
        except Exception as db_err:
            db.rollback()
            raise ValidationError(f"Database error: {str(db_err)}")

        # Launch background task for extraction and indexing
        from ..shared.config import get_settings
        db_url = get_settings().database_url
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


def _process_document_task(doc_id: int, kb_id: int, file_path_str: str, filename: str, db_url: str):
    """Background task: extract text, then index document, then update DB status."""
    from ..infrastructure.database.database import Database
    from ..core.search.dynamic_index import IndexManager
    import asyncio

    file_path = Path(file_path_str)
    
    # 1. Extraction
    try:
        print(f"BG_TASK: Starting extraction for doc {doc_id} ({filename})...")
        content = _extract_file_content_sync(file_path, filename)
        
        if content.startswith("Error"):
            print(f"BG_TASK ERROR: Extraction failed for doc {doc_id}: {content}")
            raise Exception(content)
        
        print(f"BG_TASK: Extraction complete for doc {doc_id}. Length: {len(content)} chars.")

        # 2. Update content in DB
        bg_db = Database(db_url)
        with bg_db.session() as session:
            doc_obj = session.get(Document, doc_id)
            if doc_obj:
                doc_obj.content = content
            session.commit()

        # 3. Indexing
        print(f"BG_TASK: Starting indexing for doc {doc_id}...")
        index_mgr = IndexManager(kb_id)
        success = index_mgr.create_document_index(doc_id, content)
        print(f"BG_TASK: Indexing {'successful' if success else 'failed'} for doc {doc_id}.")

        # 4. Final status update
        with bg_db.session() as session:
            doc_obj = session.get(Document, doc_id)
            if doc_obj:
                doc_obj.indexed = success
                doc_obj.index_status = "indexed" if success else "failed"
                chunk_count = len(content.split()) // 250 if content else 0
                doc_obj.chunk_count = max(chunk_count, 1) if success else 0
            session.commit()
            
    except Exception as e:
        print(f"DEBUG background processing error for doc {doc_id}: {e}")
        try:
            bg_db = Database(db_url)
            with bg_db.session() as session:
                doc_obj = session.get(Document, doc_id)
                if doc_obj:
                    doc_obj.indexed = False
                    doc_obj.index_status = "failed"
                session.commit()
        except Exception:
            pass


def _extract_file_content_sync(file_path: Path, filename: str) -> str:
    """Synchronous version of extraction for background tasks with multithreading for PDF."""
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    try:
        if ext == "txt":
            return file_path.read_text(encoding="utf-8")
        elif ext == "pdf":
            try:
                import PyPDF2
                text = []
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text.append(page.extract_text() or "")
                return "\n".join(text)
            except ImportError:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    # Use ThreadPoolExecutor for faster extraction on multi-page PDFs
                    pages = pdf.pages
                    if len(pages) > 5:
                        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                            # Extract pages in parallel
                            futures = [executor.submit(lambda p: p.extract_text() or "", page) for page in pages]
                            results = [f.result() for f in futures]
                            return "\n".join(results)
                    else:
                        return "\n".join(page.extract_text() or "" for page in pages)
        elif ext in ["doc", "docx"]:
            from docx import Document as DocxDocument
            docx = DocxDocument(file_path)
            return "\n".join(para.text for para in docx.paragraphs)
        elif ext in ["xlsx", "xls"]:
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_string()
        else:
            return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"Error extracting content: {str(e)}"


async def extract_file_content(file_path: Path, filename: str) -> str:
    """Async wrapper for the sync extraction (used by summarizer which is still async-await based)."""
    return _extract_file_content_sync(file_path, filename)


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    repo = DocumentRepository(Document, db)
    doc = repo.get_by_id(doc_id)

    if not doc or doc.user_id != current_user.id:
        raise NotFoundError("Document not found")

    # Delete index
    index_path = Path(f"data_storage/indices/{doc_id}")
    if index_path.exists():
        shutil.rmtree(index_path)

    # Delete file
    if doc.file_path:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()

    repo.delete(doc_id)
    db.commit()

    return {"status": "deleted", "id": doc_id}


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(
    req: SummarizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from ..core.services.summarizer import Summarizer

    # Get user's API key from settings
    settings_repo = UserSettingRepository(UserSetting, db)
    api_key_setting = settings_repo.get_by_user_and_key(current_user.id, "groq_api_key")
    api_key = api_key_setting.value if api_key_setting else None

    if not api_key:
        from ..shared.config import get_settings
        api_key = get_settings().groq_api_key

    # We do NOT raise an error if api_key is missing, because Summarizer
    # handles the fallback to local Ollama.

    summarizer = Summarizer()
    result = summarizer.summarize_text(req.text, api_key=api_key, max_length=req.max_length)
    
    if "error" in result:
        raise ValidationError(result["error"])

    return SummarizeResponse(
        summary=result["summary"],
        original_length=result["original_length"],
        summary_length=result["summary_length"]
    )

def cleanup_stuck_documents(db: Session):
    """Mark documents stuck in 'processing' as 'failed' or ready to resume."""
    from ..domain.models import Document
    stuck_docs = db.query(Document).filter(Document.index_status == "processing").all()
    for doc in stuck_docs:
        print(f"SYSTEM: Found stuck document {doc.id} ({doc.title}). Resetting to 'failed'.")
        doc.index_status = "failed"
    db.commit()

@router.post("/summarize/file", response_model=SummarizeResponse)
async def summarize_file(
    file: UploadFile = File(...),
    max_length: int = Form(500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    from ..core.services.summarizer import Summarizer
    
    settings_repo = UserSettingRepository(UserSetting, db)
    api_key_setting = settings_repo.get_by_user_and_key(current_user.id, "groq_api_key")
    api_key = api_key_setting.value if api_key_setting else None

    if not api_key:
        from ..shared.config import get_settings
        api_key = get_settings().groq_api_key

    # Let Summarizer handle the fallback.

    # Save temp and extract text
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
    
    # cleanup temp
    if file_path.exists():
        file_path.unlink()

    summarizer = Summarizer()
    result = summarizer.summarize_text(content, api_key=api_key, max_length=max_length)
    
    if "error" in result:
        raise ValidationError(result["error"])

    return SummarizeResponse(
        summary=result["summary"],
        original_length=result["original_length"],
        summary_length=result["summary_length"]
    )