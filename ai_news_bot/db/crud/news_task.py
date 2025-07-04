from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.news_task import NewsTask
from ai_news_bot.web.api.news_task.schema import RSSItemSchema


class NewsTaskCRUD(BaseCRUD):
    async def add_false_positive(
        self,
        news: RSSItemSchema,
        news_task_id: int,
        session: AsyncSession,
    ):
        news_task = await self.get_object_by_id(session=session, obj_id=news_task_id)
        if news_task is None:
            raise ValueError("News task not found")
        # SQLAlchemy models do not support direct assignment of lists,
        # so we need to create a new list.
        news_task.false_positives = [
            *news_task.false_positives,
            news.model_dump(mode="json"),
        ]
        session.add(news_task)
        await session.commit()
        await session.refresh(news_task)
        return news_task

    async def get_false_positives(
        self,
        news_task_id: int,
        session: AsyncSession,
    ) -> list[RSSItemSchema]:
        news_task = await self.get_object_by_id(session=session, obj_id=news_task_id)
        if news_task is None:
            raise ValueError("News task not found")
        return [RSSItemSchema(**item) for item in news_task.false_positives]


news_task_crud = NewsTaskCRUD(NewsTask)
