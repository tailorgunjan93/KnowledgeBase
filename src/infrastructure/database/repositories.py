from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Base, ChatSession, Document, KBMember, KnowledgeBase, Message, User, UserSetting

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):  # noqa: UP046
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> ModelType | None:
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
    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(self.model).where(self.model.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(self.model).where(self.model.email == email))
        return result.scalar_one_or_none()

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(self.model.id)))
        return result.scalar_one()

    async def get_all_paginated(self, skip: int = 0, limit: int = 50) -> Sequence[User]:
        result = await self.session.scalars(
            select(self.model).order_by(self.model.created_at.asc()).offset(skip).limit(limit)
        )
        return result.all()


class UserSettingRepository(BaseRepository[UserSetting]):
    async def get_by_user_and_key(self, user_id: int, key: str) -> UserSetting | None:
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
        """Legacy: fetch KBs owned directly by user_id (used for owner backfill)."""
        result = await self.session.scalars(
            select(self.model)
            .where(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        return result.all()

    async def get_by_member(self, user_id: int, skip: int = 0, limit: int = 20) -> Sequence[KnowledgeBase]:
        """Fetch KBs where user is a member (any role)."""
        result = await self.session.scalars(
            select(self.model)
            .join(KBMember, (KBMember.kb_id == self.model.id) & (KBMember.user_id == user_id))
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        return result.all()

    async def get_all_kbs(self, skip: int = 0, limit: int = 20) -> Sequence[KnowledgeBase]:
        """Admin: fetch all KBs."""
        result = await self.session.scalars(
            select(self.model)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        return result.all()

    async def get_by_user_and_id(self, kb_id: int, user_id: int) -> KnowledgeBase | None:
        """Legacy ownership check — used in documents.py where we do per-ownership guard."""
        result = await self.session.execute(select(self.model).where(
            self.model.id == kb_id,
            self.model.user_id == user_id
        ))
        return result.scalar_one_or_none()

    async def get_by_id_accessible(self, kb_id: int, user_id: int, is_admin: bool = False) -> KnowledgeBase | None:
        """Fetch KB if user is a member OR is admin."""
        kb = await self.get_by_id(kb_id)
        if not kb:
            return None
        if is_admin:
            return kb
        member_repo = KBMemberRepository(KBMember, self.session)
        member = await member_repo.get(kb_id, user_id)
        return kb if member else None

    async def count_by_user(self, user_id: int) -> int:
        """Count KBs where user is a member."""
        result = await self.session.execute(
            select(func.count(self.model.id))
            .join(KBMember, (KBMember.kb_id == self.model.id) & (KBMember.user_id == user_id))
        )
        return result.scalar_one()

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(self.model.id)))
        return result.scalar_one()

    async def get_with_counts(self, user_id: int, skip: int = 0, limit: int = 20) -> Sequence[tuple]:
        """Fetch KBs (member-based) with document counts and member's role."""
        stmt = (
            select(self.model, func.count(Document.id), KBMember.role)
            .join(KBMember, (KBMember.kb_id == self.model.id) & (KBMember.user_id == user_id))
            .outerjoin(Document, self.model.id == Document.kb_id)
            .group_by(self.model.id, KBMember.role)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def get_with_counts_admin(self, skip: int = 0, limit: int = 20) -> Sequence[tuple]:
        """Admin: all KBs with document counts."""
        stmt = (
            select(self.model, func.count(Document.id))
            .outerjoin(Document, self.model.id == Document.kb_id)
            .group_by(self.model.id)
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.all()


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
            self.model.indexed.is_(True),
        ))
        return result.scalar_one()

    async def get_pending_indexing(self, kb_id: int) -> Sequence[Document]:
        result = await self.session.scalars(select(self.model).where(
            self.model.kb_id == kb_id,
            self.model.indexed.is_(False),
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

    async def get_by_user_and_id(self, session_id: int, user_id: int) -> ChatSession | None:
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


class KBMemberRepository(BaseRepository[KBMember]):
    async def get(self, kb_id: int, user_id: int) -> KBMember | None:
        result = await self.session.execute(select(self.model).where(
            self.model.kb_id == kb_id,
            self.model.user_id == user_id
        ))
        return result.scalar_one_or_none()

    async def list_by_kb(self, kb_id: int) -> Sequence[KBMember]:
        result = await self.session.scalars(
            select(self.model)
            .where(self.model.kb_id == kb_id)
            .order_by(self.model.created_at.asc())
        )
        return result.all()

    async def upsert(self, kb_id: int, user_id: int, role: str) -> KBMember:
        member = await self.get(kb_id, user_id)
        if member:
            member.role = role
            await self.session.flush()
            return member
        return await self.create(kb_id=kb_id, user_id=user_id, role=role)

    async def remove(self, kb_id: int, user_id: int) -> bool:
        member = await self.get(kb_id, user_id)
        if member:
            await self.session.delete(member)
            return True
        return False
