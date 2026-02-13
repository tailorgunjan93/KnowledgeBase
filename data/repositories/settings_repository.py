"""Skills and Settings repository implementations."""
from typing import List, Optional
from domain.models import Skill, Setting
from data.repositories.base_repository import BaseRepository
from data.db_context import db_context


class SkillRepository(BaseRepository[Skill]):
    """Repository for Skill entity."""
    
    def __init__(self):
        super().__init__(Skill, "skills")

    def get_user_skills(self, user_id: int) -> List[Skill]:
        """Get all skills for a user."""
        sql = f"SELECT * FROM {self.table_name} WHERE user_id = ? ORDER BY created_at DESC"
        with db_context.session() as conn:
            cursor = conn.execute(sql, (user_id,))
            return [self.model_class(**dict(row)) for row in cursor.fetchall()]


class SettingsRepository(BaseRepository[Setting]):
    """Repository for User Settings."""
    
    def __init__(self):
        super().__init__(Setting, "settings")

    def get_value(self, user_id: int, key: str) -> Optional[str]:
        """Get a specific setting value."""
        sql = f"SELECT value FROM {self.table_name} WHERE user_id = ? AND key = ?"
        with db_context.session() as conn:
            cursor = conn.execute(sql, (user_id, key))
            row = cursor.fetchone()
            return row['value'] if row else None

    def set_value(self, user_id: int, key: str, value: str):
        """Set a setting value (Insert or Replace)."""
        sql = f"INSERT OR REPLACE INTO {self.table_name} (user_id, key, value) VALUES (?, ?, ?)"
        with db_context.session() as conn:
            conn.execute(sql, (user_id, key, value))
