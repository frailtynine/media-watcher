import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.events import crud_event
from ai_news_bot.db.dependencies import get_db_session
from ai_news_bot.db.models.users import User, current_active_user
from ai_news_bot.settings import settings
from ai_news_bot.web.api.events.schema import (
    EventCreate,
    EventResponse,
)

router = APIRouter()


FUTURUM_URL = (
    "https://api.futurum.services/"
    "events?sort_by=new&limit=100&offset=0"
)


@router.get("/refresh", response_model=list[EventResponse])
async def refresh_events(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
):
    """
    Refresh events data.

    :return: A message indicating the refresh status.
    """
    cookies = {
        "session_id": settings.session_id,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            FUTURUM_URL,
            cookies=cookies,
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch events from Futurum API",
        )
    for item in response.json():
        event = EventCreate(**item)
        if not await crud_event.get_object_by_id(
            session=session,
            obj_id=event.id,
        ):
            await crud_event.create(session=session, obj_in=event)
    refreshed_ids = [
        event["id"] for event in response.json()
    ]
    all_events = await crud_event.delete_old_events(
        session=session,
        actual_events_ids=refreshed_ids,
    )
    return all_events


@router.get("/", response_model=list[EventResponse])
async def get_events(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> list[EventResponse]:
    """
    Get all events.

    :return: A list of events.
    """
    events = await crud_event.get_all_objects(
        session=session,
        limit=1000,
    )
    return events


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> EventResponse:
    """
    Get a specific event by ID.

    :param event_id: The ID of the event to retrieve.
    :return: The requested event.
    """
    event = await crud_event.get_object_by_id(session=session, obj_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventCreate,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> EventResponse:
    """
    Update a specific event by ID.

    :param event_id: The ID of the event to update.
    :param event_data: The updated event data.
    :return: The updated event.
    """
    event = await crud_event.get_object_by_id(session=session, obj_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event = await crud_event.update(
        session=session,
        obj_id=event_id,
        obj_in=event_data,
    )
    return event


@router.delete("/{event_id}", response_model=dict)
async def delete_event(
    event_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> dict:
    """
    Delete a specific event by ID.

    :param event_id: The ID of the event to delete.
    :return: A message indicating the deletion status.
    """
    success = await crud_event.delete_object_by_id(
        session=session,
        obj_id=event_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}


@router.get("/{event_id}/toggle_pause", response_model=EventResponse)
async def toggle_pause_event(
    event_id: str,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> EventResponse:
    """
    Toggle the pause state of a specific event by ID.

    :param event_id: The ID of the event to toggle.
    :return: The updated event.
    """
    event = await crud_event.get_object_by_id(session=session, obj_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.is_active = not event.is_active
    await session.commit()
    await session.refresh(event)
    return event
