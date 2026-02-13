"""Tests for Authentication and User Repository."""
import pytest
from data.repositories.user_repository import UserRepository
from domain.models import User
from core.security import SecurityManager

def test_create_user(clean_db):
    """Test creating a new user."""
    repo = UserRepository()
    
    password = "securepassword123"
    hashed = SecurityManager.hash_password(password)
    
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hashed
    )
    
    user_id = repo.create(user)
    assert user_id is not None
    
    # Verify retrieval
    retrieved = repo.get_by_id(user_id)
    assert retrieved is not None
    assert retrieved.username == "testuser"
    assert retrieved.email == "test@example.com"
    assert SecurityManager.verify_password(password, retrieved.password_hash)

def test_duplicate_user(clean_db):
    """Test that duplicate usernames are not allowed."""
    repo = UserRepository()
    user1 = User(username="unique", email="u1@e.com", password_hash="hash")
    repo.create(user1)
    
    user2 = User(username="unique", email="u2@e.com", password_hash="hash")
    
    with pytest.raises(Exception): # SQLite constraint violation
        repo.create(user2)

def test_get_by_email(clean_db):
    """Test retrieving user by email."""
    repo = UserRepository()
    user = User(username="finder", email="find@me.com", password_hash="hash")
    repo.create(user)
    
    found = repo.get_by_email("find@me.com")
    assert found is not None
    assert found.username == "finder"
