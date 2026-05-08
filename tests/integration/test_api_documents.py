import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.db.database import get_database
from src.db.models import Base, User, KnowledgeBase, Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import io

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_docs.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

from src.api.deps import get_db_session
app.dependency_overrides[get_db_session] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(client):
    db = TestingSessionLocal()
    user = User(username="testuser", email="test@test.com", password_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Mock auth for endpoints
    from src.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user
    
    yield user
    db.close()
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def test_kb(test_user):
    db = TestingSessionLocal()
    kb = KnowledgeBase(user_id=test_user.id, name="Test KB")
    db.add(kb)
    db.commit()
    db.refresh(kb)
    yield kb
    db.close()

def test_upload_document(client, test_user, test_kb):
    file_content = b"This is a test document content."
    files = {"file": ("test_doc.txt", io.BytesIO(file_content), "text/plain")}
    
    response = client.post(f"/api/kb/{test_kb.id}/documents", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["title"] == "test_doc.txt"
    assert "index_status" in data

def test_summarize_endpoint_with_text(client, test_user):
    from unittest.mock import patch
    with patch("src.core.services.summarizer.Summarizer.summarize_text") as mock_summarize:
        mock_summarize.return_value = {
            "summary": "Mock summary",
            "key_points": ["Point 1"],
            "original_length": 100,
            "summary_length": 20
        }
        
        response = client.post("/api/summarize", json={"text": "Long text to summarize"})
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "Mock summary"
