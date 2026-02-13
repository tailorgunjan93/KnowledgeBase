"""Base repository class implementing common CRUD operations."""
from typing import Generic, TypeVar, List, Optional, Type, Any, Dict
from pydantic import BaseModel
from data.db_context import db_context

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Abstract base repository implementing the Repository Pattern.
    Separates data access logic from business logic.
    """
    
    def __init__(self, model_class: Type[T], table_name: str):
        self.model_class = model_class
        self.table_name = table_name

    def create(self, data: BaseModel) -> Optional[int]:
        """Insert a new record."""
        # Convert Pydantic model to dict, excluding None (for defaults) and id
        values = data.model_dump(exclude={'id'}, exclude_none=True)
        columns = ', '.join(values.keys())
        placeholders = ', '.join(['?' for _ in values])
        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        with db_context.session() as conn:
            cursor = conn.execute(sql, list(values.values()))
            return cursor.lastrowid

    def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve a record by ID."""
        sql = f"SELECT * FROM {self.table_name} WHERE id = ?"
        with db_context.session() as conn:
            cursor = conn.execute(sql, (id,))
            row = cursor.fetchone()
            if row:
                return self.model_class(**dict(row))
        return None

    def get_all(self, where: Optional[Dict[str, Any]] = None) -> List[T]:
        """Retrieve all records, optionally filtered."""
        sql = f"SELECT * FROM {self.table_name}"
        params = []
        
        if where:
            conditions = [f"{k} = ?" for k in where.keys()]
            sql += " WHERE " + " AND ".join(conditions)
            params = list(where.values())
            
        with db_context.session() as conn:
            cursor = conn.execute(sql, params)
            return [self.model_class(**dict(row)) for row in cursor.fetchall()]

    def update(self, id: int, data: Dict[str, Any]) -> bool:
        """Update a record."""
        if not data:
            return False
            
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
        params = list(data.values()) + [id]
        
        with db_context.session() as conn:
            cursor = conn.execute(sql, params)
            return cursor.rowcount > 0

    def delete(self, id: int) -> bool:
        """Delete a record."""
        sql = f"DELETE FROM {self.table_name} WHERE id = ?"
        with db_context.session() as conn:
            cursor = conn.execute(sql, (id,))
            return cursor.rowcount > 0
