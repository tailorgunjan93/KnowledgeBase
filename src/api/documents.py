from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import shutil
import uuid
from pathlib import Path

try:
    from .deps import get_db_session, get_current_user
    from ..db.repositories import DocumentRepository, KnowledgeBaseRepository, UserSettingRepository
    from ..db.models import Document, User, UserSetting, KnowledgeBase
    from ..shared.exceptions import NotFoundError, ValidationError
except (ImportError, ModuleNotFoundError):
    try:
        from src.api.deps import get_db_session, get_current_user
        from src.db.repositories import DocumentRepository, KnowledgeBaseRepository, UserSettingRepository
        from src.db.models import Document, User, UserSetting, KnowledgeBase
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


@router.post("/kb/{kb_id}/documents")
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    try:
        kb_repo = KnowledgeBaseRepository(KnowledgeBase, db)
        if not kb_repo.get_by_user_and_id(kb_id, current_user.id):
            return {"detail": "Knowledge base not found", "status": "error"}

        # Save uploaded file
        upload_dir = Path(f"data_storage/uploads/{kb_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        with file_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        # Extract content based on file type
        content = await extract_file_content(file_path, file.filename)

        # Create doc record
        doc_repo = DocumentRepository(Document, db)
        try:
            doc = doc_repo.create(
                kb_id=kb_id,
                user_id=current_user.id,
                title=file.filename,
                content=content if not content.startswith("Error") else "",
                file_type=file.filename.split(".")[-1] if "." in file.filename else "unknown",
                file_path=str(file_path)
            )
            db.commit()
        except Exception as db_err:
            db.rollback()
            raise ValidationError(f"Database error: {str(db_err)}")

        # Start indexing in background
        try:
            from ..core.search.dynamic_index import IndexManager
            index_mgr = IndexManager(kb_id)
            import concurrent.futures
            # Index the text content if available
            text_to_index = content if not content.startswith("Error") else ""
            if text_to_index:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    executor.submit(index_mgr.create_document_index, doc.id, text_to_index)
        except Exception as e:
            print(f"DEBUG indexing error: {e}")
        
        return {
            "id": doc.id,
            "title": doc.title,
            "status": "uploaded",
            "index_status": doc.index_status,
            "warning": content if content.startswith("Error") else None
        }
    except Exception as e:
        import traceback
        error_msg = f"UPLOAD FAILED: {str(e)} - {traceback.format_exc()}"
        print(error_msg)
        return {"detail": error_msg, "status": "error"}


async def extract_file_content(file_path: Path, filename: str) -> str:
    """Extract text content from uploaded file."""
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    try:
        if ext == "txt":
            return file_path.read_text(encoding="utf-8")
        elif ext == "pdf":
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
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

    if not api_key:
        raise ValidationError("GROQ API key not configured")

    summarizer = Summarizer()
    result = summarizer.summarize_text(req.text, api_key=api_key, max_length=req.max_length)
    
    if "error" in result:
        raise ValidationError(result["error"])

    return SummarizeResponse(
        summary=result["summary"],
        original_length=result["original_length"],
        summary_length=result["summary_length"]
    )

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

    if not api_key:
        raise ValidationError("GROQ API key not configured")

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