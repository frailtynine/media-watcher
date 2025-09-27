"""Tests for crypto analyzer get_crypto_events function."""

import uuid
from datetime import datetime

import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.ai.crypto_analyzer import get_crypto_events
from ai_news_bot.db.crud.events import crud_event
from ai_news_bot.web.api.events.schema import EventCreate


@pytest.mark.anyio
async def test_get_crypto_events_finds_matching_events(
    fastapi_app: FastAPI,
    dbsession: AsyncSession,
) -> None:
    """Test get_crypto_events finds events with matching tickers."""

    # Create test events using EventCreate schema with proper UUIDs
    bitcoin_event = EventCreate(
        id=str(uuid.uuid4()),
        title="Bitcoin reaches new high",
        description="Bitcoin analysis event",
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        results_at=datetime(2025, 12, 31, 10, 0, 0),
        ends_at=datetime(2025, 12, 30, 10, 0, 0),
        translations={},
        rules="Bitcoin rules",
    )

    ethereum_event = EventCreate(
        id=str(uuid.uuid4()),
        title="Ethereum smart contracts update",
        description="Ethereum development news",
        created_at=datetime(2025, 1, 1, 11, 0, 0),
        results_at=datetime(2025, 12, 31, 11, 0, 0),
        ends_at=datetime(2025, 12, 30, 11, 0, 0),
        translations={},
        rules="Ethereum rules",
    )

    non_crypto_event = EventCreate(
        id=str(uuid.uuid4()),
        title="General tech news",
        description="Non-crypto related event",
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        results_at=datetime(2025, 12, 31, 12, 0, 0),
        ends_at=datetime(2025, 12, 30, 12, 0, 0),
        translations={},
        rules="General rules",
    )

    # Create events in database using CRUD
    bitcoin_db_event = await crud_event.create(session=dbsession, obj_in=bitcoin_event)
    ethereum_db_event = await crud_event.create(
        session=dbsession,
        obj_in=ethereum_event,
    )
    non_crypto_db_event = await crud_event.create(
        session=dbsession,
        obj_in=non_crypto_event,
    )

    # Set events as active (is_active defaults to False)
    bitcoin_db_event.is_active = True
    ethereum_db_event.is_active = True
    non_crypto_db_event.is_active = True

    dbsession.add_all(
        [bitcoin_db_event, ethereum_db_event, non_crypto_db_event],
    )
    await dbsession.commit()

    # Test with bitcoin and ethereum tickers
    tickers = ["bitcoin", "ethereum"]
    result = await get_crypto_events(session=dbsession, tickers=tickers)

    # Should find 2 active events (bitcoin and ethereum)
    assert len(result) == 2

    # Extract titles from result (should be EventResponse objects now)
    result_titles = []
    for event in result:
        result_titles.append(event.title)

    assert "Bitcoin reaches new high" in result_titles
    assert "Ethereum smart contracts update" in result_titles

    # Should not include non-crypto events
    assert "General tech news" not in result_titles


@pytest.mark.anyio
async def test_get_crypto_events_case_insensitive_matching(
    fastapi_app: FastAPI,
    dbsession: AsyncSession,
) -> None:
    """Test that ticker matching is case insensitive."""

    # Create event with mixed case
    event_id = str(uuid.uuid4())
    mixed_case_event = EventCreate(
        id=event_id,
        title="BITCOIN and ethereum News Update",
        description="Mixed case crypto event",
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        results_at=datetime(2025, 12, 31, 10, 0, 0),
        ends_at=datetime(2025, 12, 30, 10, 0, 0),
        translations={},
        rules="Mixed case rules",
    )

    await crud_event.create(session=dbsession, obj_in=mixed_case_event)

    # Set event as active
    event = await crud_event.get_object_by_id(session=dbsession, obj_id=event_id)
    event.is_active = True
    dbsession.add(event)
    await dbsession.commit()

    # Test with lowercase tickers
    tickers = ["bitcoin", "ethereum"]
    result = await get_crypto_events(session=dbsession, tickers=tickers)

    # Should find the mixed case event
    assert len(result) == 1
    assert result[0].title == "BITCOIN and ethereum News Update"


@pytest.mark.anyio
async def test_get_crypto_events_with_empty_tickers(
    fastapi_app: FastAPI,
    dbsession: AsyncSession,
) -> None:
    """Test behavior with empty tickers list."""

    # Create a test event
    test_event = EventCreate(
        id=str(uuid.uuid4()),
        title="Some crypto event",
        description="Test event",
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        results_at=datetime(2025, 12, 31, 10, 0, 0),
        ends_at=datetime(2025, 12, 30, 10, 0, 0),
        translations={},
        rules="Test rules",
    )

    await crud_event.create(session=dbsession, obj_in=test_event)

    # Test with empty tickers list
    result = await get_crypto_events(session=dbsession, tickers=[])

    # Should return empty list since no tickers to match
    assert len(result) == 0


@pytest.mark.anyio
async def test_get_crypto_events_with_no_matching_events(
    fastapi_app: FastAPI,
    dbsession: AsyncSession,
) -> None:
    """Test when no events match the provided tickers."""

    # Create non-matching event
    non_crypto_event = EventCreate(
        id=str(uuid.uuid4()),
        title="Weather news update",
        description="No crypto content",
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        results_at=datetime(2025, 12, 31, 10, 0, 0),
        ends_at=datetime(2025, 12, 30, 10, 0, 0),
        translations={},
        rules="Weather rules",
    )

    await crud_event.create(session=dbsession, obj_in=non_crypto_event)

    # Search for crypto tickers
    tickers = ["bitcoin", "ethereum", "dogecoin"]
    result = await get_crypto_events(session=dbsession, tickers=tickers)

    # Should return empty list
    assert len(result) == 0


@pytest.mark.anyio
async def test_get_crypto_events_partial_ticker_matching(
    fastapi_app: FastAPI,
    dbsession: AsyncSession,
) -> None:
    """Test that partial ticker names in titles are matched."""

    # Create event with partial ticker name
    event_id = str(uuid.uuid4())
    partial_match_event = EventCreate(
        id=event_id,
        title="The bitcoins are rising in value",
        description="Event with partial ticker match",
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        results_at=datetime(2025, 12, 31, 10, 0, 0),
        ends_at=datetime(2025, 12, 30, 10, 0, 0),
        translations={},
        rules="Partial match rules",
    )

    await crud_event.create(session=dbsession, obj_in=partial_match_event)

    # Set event as active
    event = await crud_event.get_object_by_id(session=dbsession, obj_id=event_id)
    event.is_active = True
    dbsession.add(event)
    await dbsession.commit()

    # Search for "bitcoin" ticker
    tickers = ["bitcoin"]
    result = await get_crypto_events(session=dbsession, tickers=tickers)

    # Should find the event since "bitcoin" is contained in "bitcoins"
    assert len(result) == 1
    assert result[0].title == "The bitcoins are rising in value"
