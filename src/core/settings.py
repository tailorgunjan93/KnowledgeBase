from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    # Encryption (AES-256-GCM for API keys at rest)
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    encryption_key: str | None = None

    # JWT
    jwt_secret: str = "dev-secret-change-in-production-12345678901234567890"
    jwt_algorithm: str = "HS256"
    jwt_expiration_days: int = 7

    # Database
    db_url: str = "sqlite:///data_storage/knowledge_base.db"

    # Active provider
    active_provider: str = "groq"

    # Groq
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"
    summarizer_model: str = "llama-3.1-8b-instant"

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Google Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    # NVIDIA NIM
    nvidia_api_key: str | None = None
    nvidia_model: str = "meta/llama-3.1-8b-instruct"

    # AWS Bedrock
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    aws_model: str = "anthropic.claude-3-haiku-20240307-v1:0"

    # Serper (Google Search API)
    serper_api_key: str | None = None

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Embedder
    embedder_model: str = "all-MiniLM-L6-v2"

    # FAISS quantization
    # QT_8bit  → 4× memory reduction, ~1% recall loss  (recommended)
    # QT_4bit  → 8× memory reduction, ~3% recall loss
    # Disable by setting faiss_quantize=false (falls back to IndexFlatL2)
    faiss_quantize: bool = True
    faiss_quantize_type: str = "sq8"   # "sq8" | "sq4"

    # Celery — async document indexing workers
    # Leave empty to fall back to FastAPI BackgroundTasks (no Redis needed).
    celery_broker_url: str = ""      # e.g. redis://localhost:6379/0
    celery_result_backend: str = ""  # e.g. redis://localhost:6379/0

    # RAG Config
    confidence_threshold: float = 0.5
    max_retries: int = 2
    enable_web_search: bool = True

    # App
    app_name: str = "Knowledge Base API"
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
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
