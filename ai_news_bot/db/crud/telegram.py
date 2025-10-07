from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.telegram import TelegramUser


class TelegramUserCRUD(BaseCRUD):
    async def get_all_chat_ids(
        self,
        session: AsyncSession,
    ) -> list[int]:
        """
        Get all Telegram chat IDs from the database.

        :param session: SQLAlchemy async session.
        :return: List of Telegram chat IDs.
        """
        query = await self.get_all_objects(session=session)
        return [user.tg_chat_id for user in query]

    async def create(
        self,
        session: AsyncSession,
        obj_in
    ):
        stmt = select(self.model).where(
            self.model.tg_id == obj_in.tg_id
        ).where(
            self.model.tg_chat_id == obj_in.tg_chat_id
        )
        existing_user = await session.execute(stmt)
        existing_user = existing_user.scalar_one_or_none()
        if not existing_user:
            return await super().create(session, obj_in)

    async def delete_user(self, session: AsyncSession, tg_id: int) -> bool:
        """
        Delete a Telegram user by their ID.

        :param session: SQLAlchemy async session.
        :param tg_id: Telegram user ID.
        """
        user = await self.get_object_by_field(
            session=session,
            field_name="tg_id",
            field_value=tg_id,
        )
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False


telegram_user_crud = TelegramUserCRUD(TelegramUser)
