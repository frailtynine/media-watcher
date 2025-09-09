from datetime import datetime
import uuid

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.base import Base
from ai_news_bot.db.models.users import User


class BaseCRUD:
    """Base CRUD class."""

    def __init__(self, model: type[Base]) -> None:
        self.model = model

    async def create(
        self,
        session: AsyncSession,
        obj_in: type[BaseModel],
        user: User | None = None,
    ) -> None:
        """Create a new object."""
        obj_dict = obj_in.model_dump()
        if user is not None:
            obj_dict["user_id"] = user.id
        obj = self.model(**obj_dict)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def update(
        self,
        session: AsyncSession,
        obj_id: int,
        obj_in: type[BaseModel],
        user: User | None = None,
    ) -> Base | None:
        """Update object by ID."""
        obj = await self.get_object_by_id(session, obj_id)
        if not obj:
            return None
        for key, value in obj_in.model_dump(
            exclude_unset=True,
            exclude_none=True,
        ).items():
            setattr(obj, key, value)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def get_object_by_id(
        self,
        session: AsyncSession,
        obj_id: int | uuid.UUID,
        user: User | None = None,
    ) -> Base | None:
        """Get object by ID."""
        if user:
            stmt = select(self.model).where(
                self.model.id == obj_id,
                self.model.user_id == user.id,
            )
            object = await session.execute(stmt)
            return object.scalars().first()
        return await session.get(self.model, obj_id)

    async def get_all_objects(
        self,
        session: AsyncSession,
        limit: int = 1000,
        offset: int = 0,
        user: User | None = None,
    ) -> list[Base]:
        """Get all objects."""
        if user:
            stmt = (
                select(self.model)
                .where(self.model.user_id == user.id)
                .limit(limit)
                .offset(offset)
            )
        else:
            stmt = select(self.model).limit(limit).offset(offset)
        query = await session.execute(stmt)
        return query.scalars().all()

    async def get_object_by_field(
        self,
        session: AsyncSession,
        field_name: str,
        field_value: str,
    ) -> Base | None:
        """Get object by field."""
        stmt = select(self.model).where(getattr(self.model, field_name) == field_value)
        query = await session.execute(stmt)
        return query.scalars().first()

    async def delete_object_by_id(
        self,
        session: AsyncSession,
        obj_id: int | str | uuid.UUID,
        user: User | None = None,
    ) -> bool:
        """Delete object by ID."""
        obj = await self.get_object_by_id(session, obj_id, user)
        if not obj:
            return False
        await session.delete(obj)
        await session.commit()
        return True

    async def get_active_tasks(self, session: AsyncSession):
        """Get all active tasks.

        Works only with Task models.
        """
        stmt = select(self.model).where(
            self.model.is_active.is_(True),
            self.model.end_date > datetime.now(),
        )
        tasks = await session.execute(stmt)
        return tasks.scalars().all()

    async def stop_task(
        self,
        news_task_id: int | uuid.UUID,
        session: AsyncSession,
    ):
        """Stop a Task by ID.

        Works only with Task moodels.
        """
        news_task = await self.get_object_by_id(session=session, obj_id=news_task_id)
        if news_task is None:
            raise ValueError("Task not found")
        news_task.is_active = False
        session.add(news_task)
        await session.commit()
        await session.refresh(news_task)
        return news_task
