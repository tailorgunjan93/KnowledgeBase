from typing import Generic, TypeVar, Type, Optional, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .models import Base, User, UserSetting, KnowledgeBase, Document, ChatSession, Message

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        return await self.session.get(self.model, id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = await self.session.scalars(
            select(self.model).offset(skip).limit(limit)
        )
        return result.all()

    async def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete(self, id: int) -> bool:
        instance = await self.get_by_id(id)
        if instance:
            await self.session.delete(instance)
            return True
        return False


class UserRepository(BaseRepository[User]):
    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(select(self.model).where(self.model.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(self.model).where(self.model.email == email))
        return result.scalar_one_or_none()


class UserSettingRepository(BaseRepository[UserSetting]):
    async def get_by_user_and_key(self, user_id: int, key: str) -> Optional[UserSetting]:
        result = await self.session.execute(select(self.model).where(
            self.model.user_id == user_id,
            self.model.key == key
        ))
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: int) -> Sequence[UserSetting]:
        result = await self.session.scalars(select(self.model).where(self.model.user_id == user_id))
        return result.all()

    async def upsert(self, user_id: int, key: str, value: str) -> UserSetting:
        setting = await self.get_by_user_and_key(user_id, key)
        if setting:
            setting.value = value
            await self.session.flush()
            return setting
        return await self.create(user_id=user_id, key=key, value=value)


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> Sequence[KnowledgeBase]:
        result = await self.session.scalars(
            select(self.model)
            .where(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        return result.all()

    async def get_by_user_and_id(self, kb_id: int, user_id: int) -> Optional[KnowledgeBase]:
        result = await self.session.execute(select(self.model).where(
            self.model.id == kb_id,
            self.model.user_id == user_id
        ))
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: int) -> int:
        result = await self.session.execute(select(func.count(self.model.id)).where(self.model.user_id == user_id))
        return result.scalar_one()


class DocumentRepository(BaseRepository[Document]):
    async def get_by_kb(self, kb_id: int, skip: int = 0, limit: int = 100) -> Sequence[Document]:
        result = await self.session.scalars(
            select(self.model)
            .where(self.model.kb_id == kb_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        return result.all()

    async def get_indexed_count(self, kb_id: int) -> int:
        result = await self.session.execute(select(func.count(self.model.id)).where(
            self.model.kb_id == kb_id,
            self.model.indexed == True
        ))
        return result.scalar_one()

    async def get_pending_indexing(self, kb_id: int) -> Sequence[Document]:
        result = await self.session.scalars(select(self.model).where(
            self.model.kb_id == kb_id,
            self.model.indexed == False
        ))
        return result.all()


class ChatSessionRepository(BaseRepository[ChatSession]):
    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> Sequence[ChatSession]:
        result = await self.session.scalars(
            select(self.model)
            .where(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.updated_at.desc())
        )
        return result.all()

    async def get_by_user_and_id(self, session_id: int, user_id: int) -> Optional[ChatSession]:
        result = await self.session.execute(select(self.model).where(
            self.model.id == session_id,
            self.model.user_id == user_id
        ))
        return result.scalar_one_or_none()


class MessageRepository(BaseRepository[Message]):
    async def get_by_session(self, session_id: int, skip: int = 0, limit: int = 100) -> Sequence[Message]:
        result = await self.session.scalars(
            select(self.model)
            .where(self.model.session_id == session_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.asc())
        )
        return result.all()
