from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator

class AppSettings(BaseSettings):
    # JWT
    jwt_secret: str = "dev-secret-change-in-production-12345678901234567890"
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7

    # Database
    db_url: str = "sqlite:///data_storage/knowledge_base.db"

    # Groq API
    groq_api_key: Optional[str] = None
    groq_model: str = "mixtral-8x7b-32768"
    summarizer_model: str = "llama-3.1-8b-instant"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Embedder
    embedder_model: str = "all-MiniLM-L6-v2"

    # RAG Config
    confidence_threshold: float = 0.5
    max_retries: int = 2
    enable_web_search: bool = True

    # App
    app_name: str = "Knowledge Base API"
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse comma-separated CORS origins from .env file."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "enable_decoding": False,  # Disable auto-JSON parsing for env vars
    }

@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
