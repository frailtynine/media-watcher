from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.events import Event
from ai_news_bot.web.api.news_task.schema import RSSItemSchema


class EventCRUD(BaseCRUD):
    """CRUD operations for Event model."""

    async def _add_item_to_list(
        self,
        news: RSSItemSchema,
        event_id: int,
        session: AsyncSession,
        list_attribute: str,
    ) -> Event:
        """Helper method to add an item to a specified list attribute."""
        event = await self.get_object_by_id(
            session=session,
            obj_id=event_id,
        )
        if event is None:
            raise ValueError("Event not found")

        # Get current list and add new item
        current_list = getattr(event, list_attribute)
        setattr(event, list_attribute, [
            *current_list,
            news.model_dump(mode="json"),
        ])

        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    async def add_false_positive(
        self,
        news: RSSItemSchema,
        event_id: int,
        session: AsyncSession,
    ):
        return await self._add_item_to_list(
            news, event_id, session, "false_positives",
        )

    async def add_positive(
        self,
        news: RSSItemSchema,
        event_id: int,
        session: AsyncSession,
    ) -> Event:
        return await self._add_item_to_list(
            news, event_id, session, "positives",
        )

    async def get_false_positives(
        self,
        event_id: int,
        session: AsyncSession,
    ) -> list[RSSItemSchema]:
        event: Event = await self.get_object_by_id(
            session=session,
            obj_id=event_id,
        )
        if event is None:
            raise ValueError("Event not found")
        return [RSSItemSchema(**item) for item in event.false_positives]

    async def get_active_tasks(self, session: AsyncSession):
        """Get all active Events."""
        stmt = select(self.model).where(
            self.model.is_active.is_(True),
            self.model.ends_at > datetime.now(),
        )
        tasks = await session.execute(stmt)
        return tasks.scalars().all()

    async def delete_old_events(
        self,
        session: AsyncSession,
        actual_events_ids: list[str],
    ) -> list[Event]:
        """
        Delete events that are not in the list of actual event IDs.
        :param session: Database session.
        :param actual_events_ids: List of actual event IDs.
        """
        stmt = select(self.model).where(
            self.model.id.not_in(actual_events_ids),
        )
        events_to_delete = await session.execute(stmt)
        events_to_delete = events_to_delete.scalars().all()
        for event in events_to_delete:
            await self.delete_object_by_id(
                session=session,
                obj_id=event.id,
            )
        all_events = await self.get_all_objects(
            session=session,
            limit=1000,
        )
        sorted_events = sorted(
            all_events,
            key=lambda x: x.ends_at,
        )
        return sorted_events


crud_event = EventCRUD(Event)
