from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from .deps import get_db_session, get_current_user
from ..infrastructure.database.repositories import UserRepository, UserSettingRepository
from ..domain.models import User, UserSetting
from ..shared.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])


class SignupRequest(BaseModel):
    username: str
    email: Optional[str] = None
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None


class TokenResponse(BaseModel):
    user_id: int
    username: str
    token: str


@router.post("/register", response_model=TokenResponse)
async def register(req: SignupRequest, db: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(User, db)

    if await repo.get_by_username(req.username):
        raise HTTPException(400, "Username already exists")

    email = req.email.strip() if req.email else None
    user = await repo.create(
        username=req.username,
        email=email,
        password_hash=hash_password(req.password)
    )

    # Create default settings
    settings_repo = UserSettingRepository(UserSetting, db)
    for key in ["groq_api_key", "groq_model"]:
        await settings_repo.upsert(user.id, key, "")

    await db.commit()
    token = create_access_token(user.id)

    return TokenResponse(user_id=user.id, username=user.username, token=token)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(User, db)
    user = await repo.get_by_username(req.username)

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(user.id)

    return TokenResponse(user_id=user.id, username=user.username, token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email
    )


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.get("/settings")
async def get_settings_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    repo = UserSettingRepository(UserSetting, db)
    settings = await repo.get_all_for_user(current_user.id)
    return {s.key: s.value for s in settings}


@router.post("/settings")
async def update_settings(
    req: SettingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    repo = UserSettingRepository(UserSetting, db)
    await repo.upsert(current_user.id, req.key, req.value)
    await db.commit()
    return {"status": "ok"}