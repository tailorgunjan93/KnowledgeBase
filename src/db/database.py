from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from pathlib import Path

from .models import Base


class Database:
    def __init__(self, database_url: str):
        connect_args = {}
        if database_url.startswith("sqlite"):
            # Ensure directory exists for SQLite
            db_path = database_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            connect_args["check_same_thread"] = False

        self.engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    def create_all(self):
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def get_database() -> Database:
    from ..shared.config import get_settings
    return Database(get_settings().database_url)
