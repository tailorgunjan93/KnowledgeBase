from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .models import Base, User, UserSetting, KnowledgeBase, Document, ChatSession, Message

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id: int) -> Optional[ModelType]:
        return self.session.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return list(
            self.session.scalars(
                select(self.model).offset(skip).limit(limit)
            ).all()
        )

    def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance

    def delete(self, id: int) -> bool:
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            return True
        return False


class UserRepository(BaseRepository[User]):
    def get_by_username(self, username: str) -> Optional[User]:
        return self.session.scalar(
            select(self.model).where(self.model.username == username)
        )

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.scalar(
            select(self.model).where(self.model.email == email)
        )


class UserSettingRepository(BaseRepository[UserSetting]):
    def get_by_user_and_key(self, user_id: int, key: str) -> Optional[UserSetting]:
        return self.session.scalar(
            select(self.model).where(
                self.model.user_id == user_id,
                self.model.key == key
            )
        )

    def get_all_for_user(self, user_id: int) -> List[UserSetting]:
        return list(
            self.session.scalars(
                select(self.model).where(self.model.user_id == user_id)
            ).all()
        )

    def upsert(self, user_id: int, key: str, value: str) -> UserSetting:
        setting = self.get_by_user_and_key(user_id, key)
        if setting:
            setting.value = value
            self.session.flush()
            return setting
        return self.create(user_id=user_id, key=key, value=value)


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> List[KnowledgeBase]:
        return list(
            self.session.scalars(
                select(self.model)
                .where(self.model.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .order_by(self.model.created_at.desc())
            ).all()
        )

    def get_by_user_and_id(self, kb_id: int, user_id: int) -> Optional[KnowledgeBase]:
        return self.session.scalar(
            select(self.model).where(
                self.model.id == kb_id,
                self.model.user_id == user_id
            )
        )

    def count_by_user(self, user_id: int) -> int:
        return self.session.scalar(
            select(func.count(self.model.id)).where(self.model.user_id == user_id)
        )


class DocumentRepository(BaseRepository[Document]):
    def get_by_kb(self, kb_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
        return list(
            self.session.scalars(
                select(self.model)
                .where(self.model.kb_id == kb_id)
                .offset(skip)
                .limit(limit)
                .order_by(self.model.created_at.desc())
            ).all()
        )

    def get_indexed_count(self, kb_id: int) -> int:
        return self.session.scalar(
            select(func.count(self.model.id)).where(
                self.model.kb_id == kb_id,
                self.model.indexed == True
            )
        )

    def get_pending_indexing(self, kb_id: int) -> List[Document]:
        return list(
            self.session.scalars(
                select(self.model).where(
                    self.model.kb_id == kb_id,
                    self.model.indexed == False
                )
            ).all()
        )


class ChatSessionRepository(BaseRepository[ChatSession]):
    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> List[ChatSession]:
        return list(
            self.session.scalars(
                select(self.model)
                .where(self.model.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .order_by(self.model.updated_at.desc())
            ).all()
        )

    def get_by_user_and_id(self, session_id: int, user_id: int) -> Optional[ChatSession]:
        return self.session.scalar(
            select(self.model).where(
                self.model.id == session_id,
                self.model.user_id == user_id
            )
        )


class MessageRepository(BaseRepository[Message]):
    def get_by_session(self, session_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        return list(
            self.session.scalars(
                select(self.model)
                .where(self.model.session_id == session_id)
                .offset(skip)
                .limit(limit)
                .order_by(self.model.created_at.asc())
            ).all()
        )
