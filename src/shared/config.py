from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from typing import Optional, List
import json


class Settings(BaseSettings):
    # JWT - MUST be required, no fallback
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7

    # Database
    database_url: str = "sqlite:///data_storage/knowledge_base.db"

    # CORS - stored as string, parsed to list via property
    cors_origins: str = "http://localhost:3000"
    cors_allow_credentials: bool = True

    # Rate limiting
    rate_limit_per_minute: int = 60

    # App
    app_name: str = "Knowledge Base API"
    debug: bool = False
    log_level: str = "INFO"

    # Groq API
    groq_api_key: Optional[str] = None
    groq_model: str = "openai/gpt-oss-120b"

    # Web Search
    enable_web_search: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse cors_origins string into a list."""
        val = self.cors_origins.strip()
        # Handle JSON array format
        if val.startswith("["):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass
        # Handle comma-separated format
        return [origin.strip() for origin in val.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
