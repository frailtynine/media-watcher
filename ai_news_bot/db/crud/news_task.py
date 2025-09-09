from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.news_task import NewsTask
from ai_news_bot.web.api.news_task.schema import RSSItemSchema


class NewsTaskCRUD(BaseCRUD):
    """CRUD operations for NewsTask model."""

    async def _add_item_to_list(
        self,
        news: RSSItemSchema,
        news_task_id,
        session: AsyncSession,
        list_attribute: str,
    ) -> NewsTask:
        """Helper method to add an item to a specified list attribute."""
        news_task = await self.get_object_by_id(
            session=session,
            obj_id=news_task_id,
        )
        if news_task is None:
            raise ValueError("News task not found")

        # Get current list and add new item
        current_list = getattr(news_task, list_attribute)
        setattr(news_task, list_attribute, [
            *current_list,
            news.model_dump(mode="json"),
        ])

        session.add(news_task)
        await session.commit()
        await session.refresh(news_task)
        return news_task

    async def add_false_positive(
        self,
        news: RSSItemSchema,
        news_task_id,
        session: AsyncSession,
    ):
        return await self._add_item_to_list(
            news, news_task_id, session, "false_positives",
        )

    async def add_positive(
        self,
        news: RSSItemSchema,
        news_task_id: int,
        session: AsyncSession,
    ) -> NewsTask:
        return await self._add_item_to_list(
            news, news_task_id, session, "positives",
        )

    async def get_false_positives(
        self,
        news_task_id: int,
        session: AsyncSession,
    ) -> list[RSSItemSchema]:
        news_task = await self.get_object_by_id(
            session=session,
            obj_id=news_task_id,
        )
        if news_task is None:
            raise ValueError("News task not found")
        return [RSSItemSchema(**item) for item in news_task.false_positives]


news_task_crud = NewsTaskCRUD(NewsTask)
