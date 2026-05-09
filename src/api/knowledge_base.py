from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from .deps import get_db_session, get_current_user, get_pagination_params
from ..infrastructure.database.repositories import KnowledgeBaseRepository, DocumentRepository
from ..domain.models import KnowledgeBase, Document, User
from ..shared.exceptions import NotFoundError
import shutil
from pathlib import Path

router = APIRouter(prefix="/api/kb", tags=["knowledge_bases"])


class CreateKBRequest(BaseModel):
    name: str
    description: str = ""


class KBResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_public: bool = False
    document_count: int = 0


class KBListResponse(BaseModel):
    items: List[KBResponse]
    total: int
    skip: int
    limit: int


@router.get("", response_model=KBListResponse)
def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    skip: int = 0,
    limit: int = 20
):
    skip, limit = get_pagination_params(skip, limit)
    repo = KnowledgeBaseRepository(KnowledgeBase, db)
    kbs = repo.get_by_user(current_user.id, skip=skip, limit=limit)
    total = repo.count_by_user(current_user.id)

    items = []
    doc_repo = DocumentRepository(Document, db)
    for kb in kbs:
        doc_count = len(doc_repo.get_by_kb(kb.id))
        items.append(KBResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            is_public=kb.is_public,
            document_count=doc_count
        ))

    return KBListResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=KBResponse)
def create_kb(
    req: CreateKBRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    repo = KnowledgeBaseRepository(KnowledgeBase, db)
    kb = repo.create(
        user_id=current_user.id,
        name=req.name,
        description=req.description
    )
    db.commit()

    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        is_public=kb.is_public,
        document_count=0
    )


@router.get("/{kb_id}", response_model=KBResponse)
def get_kb(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    repo = KnowledgeBaseRepository(KnowledgeBase, db)
    kb = repo.get_by_user_and_id(kb_id, current_user.id)

    if not kb:
        raise NotFoundError("Knowledge base not found")

    doc_repo = DocumentRepository(Document, db)
    doc_count = len(doc_repo.get_by_kb(kb_id))

    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        is_public=kb.is_public,
        document_count=doc_count
    )


@router.delete("/{kb_id}")
def delete_kb(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    repo = KnowledgeBaseRepository(KnowledgeBase, db)
    kb = repo.get_by_user_and_id(kb_id, current_user.id)

    if not kb:
        raise NotFoundError("Knowledge base not found")

    # Cascade delete documents and indices
    doc_repo = DocumentRepository(Document, db)
    docs = doc_repo.get_by_kb(kb_id)

    for doc in docs:
        index_path = Path(f"data_storage/indices/{doc.id}")
        if index_path.exists():
            shutil.rmtree(index_path)
        doc_repo.delete(doc.id)

    repo.delete(kb_id)
    db.commit()

    return {"status": "deleted", "id": kb_id}