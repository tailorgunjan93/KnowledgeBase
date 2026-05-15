import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.models import Base
from src.domain.models import User, KnowledgeBase, Document
from src.shared.security import hash_password


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create an in-memory async test database engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Yield an async database session for the test."""
    AsyncSessionLocal = sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user in the async session."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_kb(db_session, test_user):
    """Create a test knowledge base."""
    kb = KnowledgeBase(
        user_id=test_user.id,
        name="Test KB",
        description="A test knowledge base",
    )
    db_session.add(kb)
    await db_session.commit()
    await db_session.refresh(kb)
    return kb


@pytest_asyncio.fixture
async def test_document(db_session, test_kb, test_user):
    """Create a test document."""
    doc = Document(
        kb_id=test_kb.id,
        user_id=test_user.id,
        title="Test Document",
        content="This is test content for the document.",
        file_type="txt",
        index_status="pending",
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)
    return doc
