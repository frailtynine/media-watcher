from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.crypto_task import CryptoTask


class CryptoTaskCRUD(BaseCRUD):
    async def get_active_tasks_by_ticker(
        self, session: AsyncSession, ticker: str,
    ) -> list[CryptoTask]:
        """
        Get all active tasks with given ticker.
        """
        stmt = select(self.model).where(
            self.model.is_active.is_(True),
            self.model.end_date > datetime.now(),
            self.model.ticker == ticker,
        )
        tasks = await session.execute(stmt)
        return tasks.scalars().all()


crypto_task_crud = CryptoTaskCRUD(CryptoTask)
