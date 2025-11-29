from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

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
        flag_modified(news_task, list_attribute)
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

    async def add_source_to_dict(
        self,
        session: AsyncSession,
        news_task_id: int,
        source_name: str,
        url: str,
        field_name: str,
    ) -> NewsTask:
        """Add or update an item in the settings dictionary.

        Args:
            session (AsyncSession): Database session.
            key (str): Key to add or update.
            value (str): Value to associate with the key.
            field_name (str): The name of the dictionary field to update.
                Must be either 'rss_urls' or 'tg_urls'.
        """
        if field_name not in {"rss_urls", "tg_urls"}:
            raise ValueError("Invalid field name")
        news_task = await self.get_object_by_id(
            session=session,
            obj_id=news_task_id
        )
        if news_task is None:
            raise ValueError("News task not found")
        current_dict = getattr(news_task, field_name, {})
        current_dict[source_name] = url
        setattr(news_task, field_name, current_dict)
        flag_modified(news_task, field_name)
        session.add(news_task)
        await session.flush()
        await session.refresh(news_task)
        return news_task

    async def remove_source_from_dict(
        self,
        session: AsyncSession,
        source_name: str,
        field_name: str,
        news_task_id: int,
    ) -> NewsTask:
        """
        Remove an item from the settings dictionary.

        Args:
            session (AsyncSession): Database session.
            key (str): Key to remove.
            field_name (str): The name of the dictionary field to update.
                Must be either 'rss_urls' or 'tg_urls'.
        """
        if field_name not in {"rss_urls", "tg_urls"}:
            raise ValueError("Invalid field name")
        news_task = await self.get_object_by_id(
            session=session,
            obj_id=news_task_id
        )
        if news_task is None:
            raise ValueError("News task not found")
        current_dict = getattr(news_task, field_name, {})
        if source_name in current_dict:
            del current_dict[source_name]
            setattr(news_task, field_name, current_dict)
            flag_modified(news_task, field_name)
            session.add(news_task)
            await session.flush()
            await session.refresh(news_task)
        return news_task


news_task_crud = NewsTaskCRUD(NewsTask)
