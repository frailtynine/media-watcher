from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.telegram import TelegramUser

if TYPE_CHECKING:
    from ai_news_bot.db.models.news_task import NewsTask


class TelegramUserCRUD(BaseCRUD):
    async def get_all_chat_ids(
        self,
        session: AsyncSession,
        task_id: int
    ) -> list[int]:
        """
        Get all Telegram chat IDs from the database.

        :param session: SQLAlchemy async session.
        :param task_id: NewsTask ID to filter users by.
        :return: List of Telegram chat IDs.
        """
        stmt = select(self.model).where(
            self.model.tasks.any(id=task_id)
        )
        query = await session.execute(stmt)
        query = query.scalars().all()
        return [user.tg_chat_id for user in query]

    async def get_or_create(
        self,
        session: AsyncSession,
        obj_in
    ) -> tuple[bool, TelegramUser]:
        """
        Get an existing TelegramUser or create a new one.

        :param session: SQLAlchemy async session.
        :param obj_in: TelegramUser instance to create if not exists.
        :return: Tuple indicating if created and the TelegramUser instance.
        """
        stmt = select(self.model).where(
            self.model.tg_id == obj_in.tg_id
        ).where(
            self.model.tg_chat_id == obj_in.tg_chat_id
        ).options(selectinload(self.model.tasks))

        existing_user = await session.execute(stmt)
        existing_user = existing_user.scalar_one_or_none()
        if existing_user:
            return False, existing_user
        await super().create(session, obj_in)
        created_user = await session.execute(stmt)
        return True, created_user.scalar_one_or_none()

    async def add_task_to_user(
        self,
        session: AsyncSession,
        tg_id: int,
        tg_chat_id: int,
        task: "NewsTask",
    ) -> TelegramUser:
        """
        Add a NewsTask to a TelegramUser.

        :param session: SQLAlchemy async session.
        :param tg_id: Telegram user ID.
        :param tg_chat_id: Telegram chat ID.
        :param task: NewsTask instance to add.
        """
        stmt = select(self.model).where(
            self.model.tg_id == tg_id
        ).where(
            self.model.tg_chat_id == tg_chat_id
        ).options(selectinload(self.model.tasks))
        user = await session.execute(stmt)
        user = user.scalar_one_or_none()
        if not user:
            raise ValueError(
                f"TelegramUser with tg_id={tg_id} not found."
            )
        if task in user.tasks:
            return user
        user.tasks.append(task)
        session.add(user)
        await session.commit()
        refreshed_user = await session.execute(stmt)
        return refreshed_user.scalar_one_or_none()

    async def remove_task_from_user(
        self,
        session: AsyncSession,
        tg_id: int,
        tg_chat_id: int,
        task: "NewsTask",
    ) -> TelegramUser:
        """
        Remove a NewsTask from a TelegramUser.

        :param session: SQLAlchemy async session.
        :param tg_id: Telegram user ID.
        :param tg_chat_id: Telegram chat ID.
        :param task: NewsTask instance to remove.
        """
        stmt = select(self.model).where(
            self.model.tg_id == tg_id
        ).where(
            self.model.tg_chat_id == tg_chat_id
        ).options(selectinload(self.model.tasks))
        user = await session.execute(stmt)
        user = user.scalar_one_or_none()
        if not user:
            raise ValueError(
                f"TelegramUser with tg_id={tg_id} not found."
            )
        if task not in user.tasks:
            return user
        user.tasks.remove(task)
        session.add(user)
        await session.commit()
        refreshed_user = await session.execute(stmt)
        return refreshed_user.scalar_one_or_none()

    async def delete_session(
        self,
        session: AsyncSession,
        tg_id: int,
        tg_chat_id: int
    ) -> bool:
        """
        Delete a Telegram user session by their ID.

        :param session: SQLAlchemy async session.
        :param tg_id: Telegram user ID.
        :param tg_chat_id: Telegram chat ID.
        """
        stmt = select(self.model).where(
            self.model.tg_id == tg_id
        ).where(
            self.model.tg_chat_id == tg_chat_id
        )
        user = await session.execute(stmt)
        user = user.scalar_one_or_none()
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False


telegram_user_crud = TelegramUserCRUD(TelegramUser)
