import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from src.db.models import User
    from src.shared.security import hash_password

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword")
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_kb(db_session, test_user):
    """Create a test knowledge base."""
    from src.db.models import KnowledgeBase

    kb = KnowledgeBase(
        user_id=test_user.id,
        name="Test KB",
        description="A test knowledge base"
    )
    db_session.add(kb)
    db_session.commit()
    return kb


@pytest.fixture
def test_document(db_session, test_kb, test_user):
    """Create a test document."""
    from src.db.models import Document

    doc = Document(
        kb_id=test_kb.id,
        user_id=test_user.id,
        title="Test Document",
        content="This is test content for the document.",
        file_type="txt"
    )
    db_session.add(doc)
    db_session.commit()
    return doc