"""Database context manager with connection pooling and WAL mode."""
import sqlite3
from contextlib import contextmanager
from typing import Generator
from core.config import settings
from domain.exceptions import DatabaseError


class DbContext:
    """
    Database context manager handling connections and transactions.
    Implements the Context Manager pattern for resource management.
    """
    
    def __init__(self):
        """Initialize with database path from settings."""
        self.db_path = settings.DB_PATH
        self._init_db()

    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if tables exist, if not, run schema
        schema_path = settings.BASE_DIR / "data" / "schema.sql"
        
        try:
            with self.session() as conn:
                # Always run schema.sql (it uses IF NOT EXISTS) to ensure all tables exist
                # This handles migrations/updates for existing databases
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
        except Exception as e:
            # If DB doesn't exist yet, session() might fail on connection if we catch it too early
            # But _get_connection creates the file.
            # Reraise as DatabaseError logic is fine, but let's be safe.
            print(f"DB Init Warning: {e}")
            # Try once more explicitly for fresh start
            with self._get_connection() as conn:
                 with open(schema_path, 'r') as f:
                        conn.executescript(f.read())

    def _get_connection(self) -> sqlite3.Connection:
        """Create and configure a new database connection."""
        try:
            conn = sqlite3.connect(
                self.db_path, 
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            # Enable Write-Ahead Logging for concurrency
            conn.execute("PRAGMA journal_mode = WAL")
            # Increase cache size
            conn.execute("PRAGMA cache_size = -64000") # 64MB
            # Set synchronous mode to NORMAL for better performance
            conn.execute("PRAGMA synchronous = NORMAL")
            
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")

    @contextmanager
    def session(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Provide a transactional scope around a series of operations.
        Automatically commits on success and rolls back on failure.
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Transaction failed: {e}")
        finally:
            conn.close()

    def execute_script(self, script_path: str):
        """Execute a SQL script file."""
        with self.session() as conn:
            try:
                with open(script_path, 'r') as f:
                    conn.executescript(f.read())
            except IOError as e:
                raise DatabaseError(f"Failed to read script file: {e}")
            except sqlite3.Error as e:
                raise DatabaseError(f"Failed to execute script: {e}")

# Singleton instance
db_context = DbContext()
