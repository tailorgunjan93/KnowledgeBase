"""Chat repository implementation."""
from typing import List
from domain.models import ChatSession, ChatMessage
from data.repositories.base_repository import BaseRepository
from data.db_context import db_context


class ChatRepository(BaseRepository[ChatSession]):
    """Repository for ChatSession entity."""
    
    def __init__(self):
        super().__init__(ChatSession, "chat_sessions")

    def get_user_sessions(self, user_id: int) -> List[ChatSession]:
        """Get all chat sessions for a user."""
        sql = f"SELECT * FROM {self.table_name} WHERE user_id = ? ORDER BY updated_at DESC"
        with db_context.session() as conn:
            cursor = conn.execute(sql, (user_id,))
            return [self.model_class(**dict(row)) for row in cursor.fetchall()]

    def update_timestamp(self, session_id: int):
        """Update the updated_at timestamp."""
        with db_context.session() as conn:
            conn.execute(
                f"UPDATE {self.table_name} SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,)
            )


class MessageRepository(BaseRepository[ChatMessage]):
    """Repository for ChatMessage entity."""
    
    def __init__(self):
        super().__init__(ChatMessage, "chat_messages")

    def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        """Get all messages for a session."""
        sql = f"SELECT * FROM {self.table_name} WHERE session_id = ? ORDER BY timestamp ASC"
        with db_context.session() as conn:
            cursor = conn.execute(sql, (session_id,))
            return [self.model_class(**dict(row)) for row in cursor.fetchall()]
