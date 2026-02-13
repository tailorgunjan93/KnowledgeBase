"""Domain models for the Knowledge Base application."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class User(BaseModel):
    """User domain model."""
    id: Optional[int] = None
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """User creation DTO."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    """User response DTO (no password)."""
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeBase(BaseModel):
    """Knowledge Base domain model."""
    id: Optional[int] = None
    user_id: int
    name: str = Field(..., min_length=1, max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class Document(BaseModel):
    """Document domain model."""
    id: Optional[int] = None
    kb_id: int
    user_id: int
    name: str
    content: str
    file_type: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Optional metadata for vector storage
    chunk_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ChatSession(BaseModel):
    """Chat Session domain model."""
    id: Optional[int] = None
    user_id: int
    kb_id: Optional[int] = None
    title: str = "New Chat"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class ChatMessage(BaseModel):
    """Chat Message domain model."""
    id: Optional[int] = None
    session_id: int
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class Skill(BaseModel):
    """Skill domain model."""
    id: Optional[int] = None
    user_id: int
    name: str
    description: Optional[str] = None
    prompt_template: str
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class Setting(BaseModel):
    """User Setting domain model."""
    id: Optional[int] = None
    user_id: int
    key: str
    value: str

    model_config = ConfigDict(from_attributes=True)
