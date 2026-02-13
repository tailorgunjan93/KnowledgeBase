"""Knowledge Base repository implementation."""
from typing import List
from domain.models import KnowledgeBase, Document
from data.repositories.base_repository import BaseRepository
from data.db_context import db_context


class KbRepository(BaseRepository[KnowledgeBase]):
    """Repository for KnowledgeBase entity."""
    
    def __init__(self):
        super().__init__(KnowledgeBase, "knowledge_bases")

    def get_user_kbs(self, user_id: int) -> List[KnowledgeBase]:
        """Get all KBs for a user."""
        sql = f"SELECT * FROM {self.table_name} WHERE user_id = ? ORDER BY created_at DESC"
        with db_context.session() as conn:
            cursor = conn.execute(sql, (user_id,))
            return [self.model_class(**dict(row)) for row in cursor.fetchall()]


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document entity."""
    
    def __init__(self):
        super().__init__(Document, "documents")

    def get_kb_documents(self, kb_id: int) -> List[Document]:
        """Get all documents in a KB."""
        sql = f"SELECT * FROM {self.table_name} WHERE kb_id = ? ORDER BY created_at DESC"
        with db_context.session() as conn:
            cursor = conn.execute(sql, (kb_id,))
            return [self.model_class(**dict(row)) for row in cursor.fetchall()]
