from datetime import datetime, timedelta
from typing import Any

import bcrypt
import jwt

from .config import get_settings


def hash_password(password: str) -> str:
    """Hash password with bcrypt (includes salt automatically)."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed.encode("utf-8")
    )


def create_access_token(user_id: int, data: dict[str, Any] = None) -> str:
    settings = get_settings()
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=settings.jwt_expiration_days),
        **(data or {})
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
