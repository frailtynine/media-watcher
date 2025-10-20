from sqlalchemy import select, false
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.news import News


class CRUDNews(BaseCRUD):
    async def get_unprocessed_news(self, session: AsyncSession) -> list[News]:
        stmt = select(
            self.model
        ).where(
            self.model.processed == false()
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def mark_news_as_processed(
        self,
        session: AsyncSession,
        news_id: int
    ) -> News | None:
        news: News = await self.get_object_by_id(session, news_id)
        if news:
            news.processed = True
            session.add(news)
            await session.flush()
            await session.refresh(news)
            return news
        return None


crud_news = CRUDNews(News)
