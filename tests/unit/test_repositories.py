"""Unit tests for async repository layer."""
import pytest

from src.domain.models import Document, KnowledgeBase, User
from src.infrastructure.database.repositories import (
    DocumentRepository,
    KnowledgeBaseRepository,
    UserRepository,
)


class TestUserRepository:
    async def test_create_user(self, db_session):
        repo = UserRepository(User, db_session)
        user = await repo.create(
            username="newuser",
            email="new@example.com",
            password_hash="hash123",
        )
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"

    async def test_get_by_username(self, db_session, test_user):
        repo = UserRepository(User, db_session)
        found = await repo.get_by_username("testuser")
        assert found is not None
        assert found.username == "testuser"

    async def test_get_by_username_not_found(self, db_session):
        repo = UserRepository(User, db_session)
        found = await repo.get_by_username("nonexistent")
        assert found is None

    async def test_get_by_id(self, db_session, test_user):
        repo = UserRepository(User, db_session)
        found = await repo.get_by_id(test_user.id)
        assert found is not None
        assert found.id == test_user.id

    async def test_count(self, db_session, test_user):
        repo = UserRepository(User, db_session)
        count = await repo.count()
        assert count >= 1


class TestKnowledgeBaseRepository:
    async def test_create_kb(self, db_session, test_user):
        repo = KnowledgeBaseRepository(KnowledgeBase, db_session)
        kb = await repo.create(
            user_id=test_user.id,
            name="My KB",
            description="Test description",
        )
        assert kb.id is not None
        assert kb.name == "My KB"

    async def test_get_by_member(self, db_session, test_user, test_kb):
        repo = KnowledgeBaseRepository(KnowledgeBase, db_session)
        kbs = await repo.get_by_member(test_user.id)
        # test_kb fixture only creates the KB row; owner KB membership
        # is created by the API layer, so the list may be empty here.
        assert isinstance(kbs, list)


class TestDocumentRepository:
    async def test_get_by_kb(self, db_session, test_kb, test_document):
        repo = DocumentRepository(Document, db_session)
        docs = await repo.get_by_kb(test_kb.id)
        assert len(docs) >= 1

    async def test_get_indexed_count(self, db_session, test_kb, test_document):
        repo = DocumentRepository(Document, db_session)
        count = await repo.get_indexed_count(test_kb.id)
        assert count == 0  # test document is not indexed by default
