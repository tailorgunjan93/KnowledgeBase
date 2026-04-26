import pytest
from src.db.repositories import UserRepository, KnowledgeBaseRepository, DocumentRepository
from src.db.models import User, KnowledgeBase, Document


class TestUserRepository:
    def test_create_user(self, db_session):
        repo = UserRepository(User, db_session)
        user = repo.create(
            username="newuser",
            email="new@example.com",
            password_hash="hash123"
        )

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"

    def test_get_by_username(self, db_session, test_user):
        repo = UserRepository(User, db_session)
        found = repo.get_by_username("testuser")
        assert found is not None
        assert found.username == "testuser"

    def test_get_by_username_not_found(self, db_session):
        repo = UserRepository(User, db_session)
        found = repo.get_by_username("nonexistent")
        assert found is None

    def test_get_by_id(self, db_session, test_user):
        repo = UserRepository(User, db_session)
        found = repo.get_by_id(test_user.id)
        assert found is not None
        assert found.id == test_user.id


class TestKnowledgeBaseRepository:
    def test_create_kb(self, db_session, test_user):
        repo = KnowledgeBaseRepository(KnowledgeBase, db_session)
        kb = repo.create(
            user_id=test_user.id,
            name="My KB",
            description="Test description"
        )

        assert kb.id is not None
        assert kb.name == "My KB"

    def test_get_by_user(self, db_session, test_user, test_kb):
        repo = KnowledgeBaseRepository(KnowledgeBase, db_session)
        kbs = repo.get_by_user(test_user.id)
        assert len(kbs) >= 1
        assert any(kb.name == "Test KB" for kb in kbs)

    def test_get_by_user_and_id(self, db_session, test_user, test_kb):
        repo = KnowledgeBaseRepository(KnowledgeBase, db_session)
        found = repo.get_by_user_and_id(test_kb.id, test_user.id)
        assert found is not None
        assert found.id == test_kb.id

    def test_get_by_user_and_id_wrong_user(self, db_session, test_kb):
        repo = KnowledgeBaseRepository(KnowledgeBase, db_session)
        found = repo.get_by_user_and_id(test_kb.id, user_id=9999)
        assert found is None

    def test_delete_kb(self, db_session, test_user, test_kb):
        repo = KnowledgeBaseRepository(KnowledgeBase, db_session)
        result = repo.delete(test_kb.id)
        assert result is True

        found = repo.get_by_id(test_kb.id)
        assert found is None


class TestDocumentRepository:
    def test_get_by_kb(self, db_session, test_kb, test_document):
        repo = DocumentRepository(Document, db_session)
        docs = repo.get_by_kb(test_kb.id)
        assert len(docs) >= 1

    def test_get_indexed_count(self, db_session, test_kb, test_document):
        repo = DocumentRepository(Document, db_session)
        count = repo.get_indexed_count(test_kb.id)
        assert count == 0  # Test document is not indexed by default