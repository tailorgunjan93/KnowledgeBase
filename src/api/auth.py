
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import User, UserSetting
from ..infrastructure.database.repositories import UserRepository, UserSettingRepository
from ..shared.encryption import SENTINEL, encrypt, is_sensitive
from ..shared.security import create_access_token, hash_password, verify_password
from .deps import get_current_user, get_db_session

router = APIRouter(prefix="/auth", tags=["authentication"])


class SignupRequest(BaseModel):
    username: str
    email: str | None = None
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str | None = None
    role: str = "user"


class TokenResponse(BaseModel):
    user_id: int
    username: str
    token: str
    role: str = "user"


@router.post("/register", response_model=TokenResponse)
async def register(req: SignupRequest, db: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(User, db)

    if await repo.get_by_username(req.username):
        raise HTTPException(400, "Username already exists")

    # First registered user becomes admin
    user_count = await repo.count()
    role = "admin" if user_count == 0 else "user"

    email = req.email.strip() if req.email else None
    user = await repo.create(
        username=req.username,
        email=email,
        password_hash=hash_password(req.password),
        role=role
    )

    # Create default settings
    settings_repo = UserSettingRepository(UserSetting, db)
    for key in [
        "active_provider",
        "groq_api_key", "groq_model",
        "openai_api_key", "openai_model",
        "gemini_api_key", "gemini_model",
        "nvidia_api_key", "nvidia_model",
        "aws_access_key_id", "aws_secret_access_key", "aws_region", "aws_model",
        "ollama_model",
    ]:
        await settings_repo.upsert(user.id, key, "")

    await db.commit()
    token = create_access_token(user.id)

    return TokenResponse(user_id=user.id, username=user.username, token=token, role=user.role)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(User, db)
    user = await repo.get_by_username(req.username)

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(user.id)

    return TokenResponse(user_id=user.id, username=user.username, token=token, role=user.role)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=getattr(current_user, "role", "user")
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

    result: dict = {}
    for s in settings:
        if is_sensitive(s.key) and s.value:
            # Never send the real key to the frontend — return sentinel instead
            result[s.key] = SENTINEL
        else:
            result[s.key] = s.value
    return result


@router.post("/settings")
async def update_settings(
    req: SettingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    repo = UserSettingRepository(UserSetting, db)

    if is_sensitive(req.key):
        # Sentinel means "no change" — frontend echoed back what we sent it
        if req.value == SENTINEL:
            return {"status": "ok", "detail": "no_change"}
        # Encrypt before persisting (empty string clears the key)
        value_to_store = encrypt(req.value) if req.value else ""
    else:
        value_to_store = req.value

    await repo.upsert(current_user.id, req.key, value_to_store)
    await db.commit()
    return {"status": "ok"}
