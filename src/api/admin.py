"""Admin-only endpoints.

All routes require global admin role (User.role == "admin").
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Optional

from .deps import get_db_session, get_current_user
from ..infrastructure.database.repositories import UserRepository, KnowledgeBaseRepository, DocumentRepository
from ..domain.models import User, KnowledgeBase, Document
from ..shared.rbac import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UserAdminResponse(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None
    role: str
    created_at: str
    is_active: bool


class UserListResponse(BaseModel):
    items: List[UserAdminResponse]
    total: int


class UpdateRoleRequest(BaseModel):
    role: str  # "user" | "admin"


class StatsResponse(BaseModel):
    total_users: int
    total_kbs: int
    total_documents: int


# ── User list ─────────────────────────────────────────────────────────────────

@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await require_admin(current_user)

    repo = UserRepository(User, db)
    users = await repo.get_all_paginated(skip=skip, limit=limit)
    total = await repo.count()

    return UserListResponse(
        items=[
            UserAdminResponse(
                user_id=u.id,
                username=u.username,
                email=u.email,
                role=getattr(u, "role", "user"),
                created_at=u.created_at.isoformat(),
                is_active=u.is_active
            )
            for u in users
        ],
        total=total
    )


# ── Change global role ────────────────────────────────────────────────────────

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    req: UpdateRoleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await require_admin(current_user)

    if req.role not in ("user", "admin"):
        raise HTTPException(400, "Role must be 'user' or 'admin'")

    repo = UserRepository(User, db)
    target = await repo.get_by_id(user_id)
    if not target:
        raise HTTPException(404, "User not found")

    # Prevent admins from demoting themselves (safety guard)
    if target.id == current_user.id and req.role != "admin":
        raise HTTPException(400, "Cannot demote yourself")

    target.role = req.role
    await db.commit()

    return {"user_id": user_id, "role": req.role}


# ── System stats ──────────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    await require_admin(current_user)

    user_repo = UserRepository(User, db)
    kb_repo = KnowledgeBaseRepository(KnowledgeBase, db)
    doc_repo = DocumentRepository(Document, db)

    total_users = await user_repo.count()
    total_kbs = await kb_repo.count_all()

    # Count all documents
    result = await db.execute(select(func.count(Document.id)))
    total_docs = result.scalar_one()

    return StatsResponse(
        total_users=total_users,
        total_kbs=total_kbs,
        total_documents=total_docs
    )
