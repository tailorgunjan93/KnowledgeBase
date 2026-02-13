"""User repository implementation."""
from typing import Optional
from domain.models import User
from data.repositories.base_repository import BaseRepository
from data.db_context import db_context


class UserRepository(BaseRepository[User]):
    """Repository for User entity."""
    
    def __init__(self):
        super().__init__(User, "users")

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self._get_unique("username", username)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self._get_unique("email", email)
    
    def _get_unique(self, field: str, value: str) -> Optional[User]:
        """Helper for unique field lookups."""
        sql = f"SELECT * FROM {self.table_name} WHERE {field} = ?"
        with db_context.session() as conn:
            cursor = conn.execute(sql, (value,))
            row = cursor.fetchone()
            if row:
                return self.model_class(**dict(row))
        return None
