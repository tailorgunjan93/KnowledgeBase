"""Database manager for SQLite operations."""
import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatabaseManager:
    """Handles all database operations for the knowledge base system."""
    
    def __init__(self, db_path: str = "knowledge_base.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with schema."""
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            conn = self.get_connection()
            conn.executescript(schema)
            conn.commit()
            conn.close()
    
    # User operations
    def create_user(self, username: str, email: str, password_hash: str) -> Optional[int]:
        """Create a new user."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    # Knowledge base operations
    def create_knowledge_base(self, user_id: int, name: str) -> int:
        """Create a new knowledge base."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO knowledge_bases (user_id, name) VALUES (?, ?)",
            (user_id, name)
        )
        conn.commit()
        kb_id = cursor.lastrowid
        conn.close()
        return kb_id
    
    def get_user_knowledge_bases(self, user_id: int) -> List[Dict]:
        """Get all knowledge bases for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM knowledge_bases WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_knowledge_base(self, kb_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific knowledge base."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM knowledge_bases WHERE id = ? AND user_id = ?",
            (kb_id, user_id)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def delete_knowledge_base(self, kb_id: int, user_id: int) -> bool:
        """Delete a knowledge base."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM knowledge_bases WHERE id = ? AND user_id = ?",
            (kb_id, user_id)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    
    # Document operations
    def add_document(self, kb_id: int, user_id: int, name: str, content: str, file_type: str) -> int:
        """Add a document to a knowledge base."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO documents (kb_id, user_id, name, content, file_type) VALUES (?, ?, ?, ?, ?)",
            (kb_id, user_id, name, content, file_type)
        )
        conn.commit()
        doc_id = cursor.lastrowid
        conn.close()
        return doc_id
    
    def get_kb_documents(self, kb_id: int, user_id: int) -> List[Dict]:
        """Get all documents in a knowledge base."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM documents WHERE kb_id = ? AND user_id = ? ORDER BY created_at DESC",
            (kb_id, user_id)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def delete_document(self, doc_id: int, user_id: int) -> bool:
        """Delete a document."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM documents WHERE id = ? AND user_id = ?",
            (doc_id, user_id)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    
    # Chat session operations
    def create_chat_session(self, user_id: int, kb_id: Optional[int], title: str) -> int:
        """Create a new chat session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_sessions (user_id, kb_id, title) VALUES (?, ?, ?)",
            (user_id, kb_id, title)
        )
        conn.commit()
        session_id = cursor.lastrowid
        conn.close()
        return session_id
    
    def get_user_chat_sessions(self, user_id: int) -> List[Dict]:
        """Get all chat sessions for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_chat_session(self, session_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific chat session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_chat_session_timestamp(self, session_id: int):
        """Update the timestamp of a chat session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,)
        )
        conn.commit()
        conn.close()
    
    def delete_chat_session(self, session_id: int, user_id: int) -> bool:
        """Delete a chat session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM chat_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    
    # Chat message operations
    def add_chat_message(self, session_id: int, role: str, content: str):
        """Add a message to a chat session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        conn.commit()
        conn.close()
        self.update_chat_session_timestamp(session_id)
    
    def get_chat_messages(self, session_id: int) -> List[Dict]:
        """Get all messages in a chat session."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # Skills operations
    def create_skill(self, user_id: int, name: str, description: str, prompt_template: str) -> int:
        """Create a new skill."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO skills (user_id, name, description, prompt_template) VALUES (?, ?, ?, ?)",
            (user_id, name, description, prompt_template)
        )
        conn.commit()
        skill_id = cursor.lastrowid
        conn.close()
        return skill_id
    
    def get_user_skills(self, user_id: int) -> List[Dict]:
        """Get all skills for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM skills WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_skill(self, skill_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific skill."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM skills WHERE id = ? AND user_id = ?",
            (skill_id, user_id)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_skill(self, skill_id: int, user_id: int, name: str, description: str, prompt_template: str) -> bool:
        """Update a skill."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE skills SET name = ?, description = ?, prompt_template = ? WHERE id = ? AND user_id = ?",
            (name, description, prompt_template, skill_id, user_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated
    
    def delete_skill(self, skill_id: int, user_id: int) -> bool:
        """Delete a skill."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM skills WHERE id = ? AND user_id = ?",
            (skill_id, user_id)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    
    # Settings operations
    def set_setting(self, user_id: int, key: str, value: str):
        """Set a user setting."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (user_id, key, value) VALUES (?, ?, ?)",
            (user_id, key, value)
        )
        conn.commit()
        conn.close()
    
    def get_setting(self, user_id: int, key: str) -> Optional[str]:
        """Get a user setting."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM settings WHERE user_id = ? AND key = ?",
            (user_id, key)
        )
        row = cursor.fetchone()
        conn.close()
        return row['value'] if row else None
    
    def get_all_settings(self, user_id: int) -> Dict[str, str]:
        """Get all settings for a user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT key, value FROM settings WHERE user_id = ?",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return {row['key']: row['value'] for row in rows}
