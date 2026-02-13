"""Pytest configuration and fixtures."""
import pytest
import os
from pathlib import Path
from core.config import settings
from data.db_context import db_context

# Override settings for testing
os.environ["DB_PATH"] = ":memory:"

@pytest.fixture(scope="session")
def test_db():
    """Setup a test database."""
    # Use a temporary file or override settings to use :memory:
    # Since DbContext uses settings.DB_PATH, we need to patch it or ensure it points to test DB.
    # For simplicity in this setup, we'll assume the environment var patch works or we modify the singleton.
    
    # Actually, let's create a fresh file for tests to test persistent connections (WAL)
    test_db_path = settings.DATA_DIR / "test_knowledge_base.db"
    if test_db_path.exists():
        test_db_path.unlink()
    
    settings.DB_PATH = test_db_path
    db_context.db_path = test_db_path
    db_context._init_db()
    
    yield db_context
    
    # Teardown
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except:
            pass

@pytest.fixture(scope="function")
def clean_db(test_db):
    """Clean data between tests."""
    with test_db.session() as conn:
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM knowledge_bases")
        conn.execute("DELETE FROM documents")
        conn.execute("DELETE FROM chat_sessions")
        conn.execute("DELETE FROM chat_messages")
    return test_db
