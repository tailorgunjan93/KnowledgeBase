"""Role-Based Access Control helpers.

Global roles (User.role):  "user" | "admin"
Per-KB roles (KBMember.role): "viewer" | "editor" | "owner"
Admins bypass all per-KB checks.
"""
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

ROLE_ORDER = {"viewer": 0, "editor": 1, "owner": 2}


async def require_admin(current_user) -> None:
    """Raise 403 if the caller is not a global admin."""
    if getattr(current_user, "role", "user") != "admin":
        raise HTTPException(403, "Admin access required")


async def get_kb_member_role(
    kb_id: int,
    user_id: int,
    db: AsyncSession,
) -> Optional[str]:
    """Return the caller's role string for a KB, or None if not a member."""
    from ..infrastructure.database.repositories import KBMemberRepository
    from ..domain.models import KBMember
    repo = KBMemberRepository(KBMember, db)
    member = await repo.get(kb_id, user_id)
    return member.role if member else None


async def require_kb_role(
    kb_id: int,
    min_role: str,
    current_user,
    db: AsyncSession,
) -> str:
    """
    Check the caller has at least `min_role` access to the KB.
    Admins bypass membership checks and get effective role "owner".
    Returns the caller's effective role string.
    Raises 403 if access is insufficient.
    """
    if getattr(current_user, "role", "user") == "admin":
        return "owner"

    role = await get_kb_member_role(kb_id, current_user.id, db)
    if role is None:
        raise HTTPException(403, "You do not have access to this knowledge base")

    if ROLE_ORDER.get(role, -1) < ROLE_ORDER.get(min_role, 0):
        raise HTTPException(403, f"Requires at least '{min_role}' role in this knowledge base")

    return role
