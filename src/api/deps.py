from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, AsyncGenerator

from ..infrastructure.database.database import Database
from ..infrastructure.database.repositories import UserRepository, UserSettingRepository
from ..domain.models import User, UserSetting
from ..shared.security import decode_access_token
from ..core.settings import get_settings


_db_instance = None

def get_database() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(get_settings().db_url)
    return _db_instance


async def get_db_session(db: Database = Depends(get_database)) -> AsyncGenerator[AsyncSession, None]:
    async with db.session() as session:
        yield session


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    if not authorization:
        raise HTTPException(401, "Missing authorization header")

    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(401, "Invalid or expired token")

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(401, "Invalid token payload")

        user_repo = UserRepository(User, db)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(401, "User not found")

        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(401, "Invalid token")


def get_pagination_params(skip: int = 0, limit: int = 20) -> tuple[int, int]:
    return skip, min(limit, 100)


def get_user_settings(user_id: int, db: AsyncSession) -> UserSettingRepository:
    return UserSettingRepository(UserSetting, db)