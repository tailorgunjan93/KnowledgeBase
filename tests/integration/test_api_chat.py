import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.db.models import Base, User, ChatSession, UserSetting
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_chat.db"
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
    user = User(username="chatuser", email="chat@test.com", password_hash="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Add a fake groq api key to user settings so LLMFactory doesn't fail
    setting = UserSetting(user_id=user.id, key="groq_api_key", value="fake_key")
    db.add(setting)
    db.commit()
    
    from src.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user
    
    yield user
    db.close()
    app.dependency_overrides.pop(get_current_user, None)

def test_chat_endpoint(client, test_user):
    from unittest.mock import patch
    
    # Mock LLMFactory so we don't actually hit Groq/Ollama
    with patch("src.api.chat.LLMFactory.create") as mock_create:
        mock_llm = mock_create.return_value
        
        # Mock RAGOrchestrator
        with patch("src.api.chat.RAGOrchestrator") as mock_rag_cls:
            mock_rag = mock_rag_cls.return_value
            mock_rag.chat.return_value = {
                "response": "Hello, how can I help?",
                "intent": "general",
                "confidence": "high",
                "sources": []
            }
            
            response = client.post("/api/chat", json={
                "message": "Hello",
                "session_id": None,
                "kb_id": None
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Hello, how can I help?"
            assert "session_id" in data
            assert data["intent"] == "general"

def test_get_sessions(client, test_user):
    db = TestingSessionLocal()
    session = ChatSession(user_id=test_user.id, title="Test Session")
    db.add(session)
    db.commit()
    db.close()
    
    response = client.get("/api/sessions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Session"
