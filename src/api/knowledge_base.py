import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import Document, KBMember, KnowledgeBase, User
from ..infrastructure.database.repositories import (
    DocumentRepository,
    KBMemberRepository,
    KnowledgeBaseRepository,
    UserRepository,
)
from ..shared.exceptions import NotFoundError
from ..shared.rbac import require_kb_role
from .deps import get_current_user, get_db_session, get_pagination_params

router = APIRouter(prefix="/api/kb", tags=["knowledge_bases"])


class CreateKBRequest(BaseModel):
    name: str
    description: str = ""


class KBResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_public: bool = False
    document_count: int = 0
    user_role: str | None = None  # caller's role in this KB


class KBListResponse(BaseModel):
    items: list[KBResponse]
    total: int
    skip: int
    limit: int


class MemberResponse(BaseModel):
    user_id: int
    username: str
    role: str


class InviteMemberRequest(BaseModel):
    username: str
    role: str = "viewer"  # viewer | editor | owner


class UpdateMemberRoleRequest(BaseModel):
    role: str


# ── List KBs ──────────────────────────────────────────────────────────────────

@router.get("", response_model=KBListResponse)
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    skip: int = 0,
    limit: int = 20
):
    skip, limit = get_pagination_params(skip, limit)
    repo = KnowledgeBaseRepository(KnowledgeBase, db)
    is_admin = getattr(current_user, "role", "user") == "admin"

    if is_admin:
        rows = await repo.get_with_counts_admin(skip=skip, limit=limit)
        total = await repo.count_all()
        items = [
            KBResponse(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                is_public=kb.is_public,
                document_count=doc_count,
                user_role="owner"
            )
            for kb, doc_count in rows
        ]
    else:
        rows = await repo.get_with_counts(current_user.id, skip=skip, limit=limit)
        total = await repo.count_by_user(current_user.id)
        items = [
            KBResponse(
                id=kb.id,
                name=kb.name,
                description=kb.description,
                is_public=kb.is_public,
                document_count=doc_count,
                user_role=role
            )
            for kb, doc_count, role in rows
        ]

    return KBListResponse(items=items, total=total, skip=skip, limit=limit)


# ── Create KB ─────────────────────────────────────────────────────────────────

@router.post("", response_model=KBResponse)
async def create_kb(
    req: CreateKBRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    repo = KnowledgeBaseRepository(KnowledgeBase, db)
    kb = await repo.create(
        user_id=current_user.id,
        name=req.name,
        description=req.description
    )
    await db.flush()

    # Auto-create owner membership for creator
    member_repo = KBMemberRepository(KBMember, db)
    await member_repo.upsert(kb.id, current_user.id, "owner")

    await db.commit()

    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        is_public=kb.is_public,
        document_count=0,
        user_role="owner"
    )


# ── Get KB ────────────────────────────────────────────────────────────────────

@router.get("/{kb_id}", response_model=KBResponse)
async def get_kb(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    user_role = await require_kb_role(kb_id, "viewer", current_user, db)

    repo = KnowledgeBaseRepository(KnowledgeBase, db)
    kb = await repo.get_by_id(kb_id)
    if not kb:
        raise NotFoundError("Knowledge base not found")

    doc_repo = DocumentRepository(Document, db)
    docs = await doc_repo.get_by_kb(kb_id)

    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        is_public=kb.is_public,
        document_count=len(docs),
        user_role=user_role
    )


# ── Delete KB ─────────────────────────────────────────────────────────────────

@router.delete("/{kb_id}")
async def delete_kb(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await require_kb_role(kb_id, "owner", current_user, db)

    repo = KnowledgeBaseRepository(KnowledgeBase, db)
    kb = await repo.get_by_id(kb_id)
    if not kb:
        raise NotFoundError("Knowledge base not found")

    # Cascade delete documents and indices
    doc_repo = DocumentRepository(Document, db)
    docs = await doc_repo.get_by_kb(kb_id)

    for doc in docs:
        index_path = Path(f"data_storage/indices/{doc.id}")
        if index_path.exists():
            shutil.rmtree(index_path)
        await doc_repo.delete(doc.id)

    await repo.delete(kb_id)
    await db.commit()

    return {"status": "deleted", "id": kb_id}


# ── Member endpoints ──────────────────────────────────────────────────────────

@router.get("/{kb_id}/members", response_model=list[MemberResponse])
async def list_members(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await require_kb_role(kb_id, "viewer", current_user, db)

    member_repo = KBMemberRepository(KBMember, db)
    members = await member_repo.list_by_kb(kb_id)

    user_repo = UserRepository(User, db)
    result = []
    for m in members:
        user = await user_repo.get_by_id(m.user_id)
        if user:
            result.append(MemberResponse(user_id=user.id, username=user.username, role=m.role))

    return result


@router.post("/{kb_id}/members", response_model=MemberResponse)
async def invite_member(
    kb_id: int,
    req: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await require_kb_role(kb_id, "owner", current_user, db)

    if req.role not in ("viewer", "editor", "owner"):
        raise HTTPException(400, "Role must be 'viewer', 'editor', or 'owner'")

    user_repo = UserRepository(User, db)
    target = await user_repo.get_by_username(req.username)
    if not target:
        raise HTTPException(404, f"User '{req.username}' not found")

    member_repo = KBMemberRepository(KBMember, db)
    member = await member_repo.upsert(kb_id, target.id, req.role)
    await db.commit()

    return MemberResponse(user_id=target.id, username=target.username, role=member.role)


@router.put("/{kb_id}/members/{user_id}", response_model=MemberResponse)
async def update_member_role(
    kb_id: int,
    user_id: int,
    req: UpdateMemberRoleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await require_kb_role(kb_id, "owner", current_user, db)

    if req.role not in ("viewer", "editor", "owner"):
        raise HTTPException(400, "Role must be 'viewer', 'editor', or 'owner'")

    member_repo = KBMemberRepository(KBMember, db)
    member = await member_repo.get(kb_id, user_id)
    if not member:
        raise HTTPException(404, "Member not found")

    user_repo = UserRepository(User, db)
    target = await user_repo.get_by_id(user_id)

    member = await member_repo.upsert(kb_id, user_id, req.role)
    await db.commit()

    return MemberResponse(user_id=user_id, username=target.username if target else str(user_id), role=member.role)


@router.delete("/{kb_id}/members/{user_id}")
async def remove_member(
    kb_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await require_kb_role(kb_id, "owner", current_user, db)

    # Cannot remove yourself if you're the last owner
    member_repo = KBMemberRepository(KBMember, db)
    members = await member_repo.list_by_kb(kb_id)
    owners = [m for m in members if m.role == "owner"]
    if user_id == current_user.id and len(owners) <= 1:
        raise HTTPException(400, "Cannot remove the last owner of a knowledge base")

    removed = await member_repo.remove(kb_id, user_id)
    if not removed:
        raise HTTPException(404, "Member not found")

    await db.commit()
    return {"status": "removed", "user_id": user_id}
