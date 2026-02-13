"""Application configuration using Pydantic Settings."""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    # App Info
    APP_NAME: str = "Knowledge Base System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data_storage"
    DB_PATH: Path = DATA_DIR / "knowledge_base.db"
    VECTOR_DIR: Path = DATA_DIR / "vectors"
    
    # Security
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"  # Used for session signing if needed
    HASH_ROUNDS: int = 12
    
    # Database
    DB_URL: str = f"sqlite:///{DB_PATH}"
    
    # Model defaults
    DEFAULT_MODEL: str = "llama-3.1-70b-versatile"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Vector Search
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Groq API (Defaults to None, user sets it)
    GROQ_API_KEY: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_dirs(self):
        """Ensure necessary directories exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.VECTOR_DIR.mkdir(parents=True, exist_ok=True)


# Singleton instance
settings = Settings()
settings.init_dirs()
