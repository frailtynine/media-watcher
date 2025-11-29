from datetime import datetime, timedelta
from unittest import mock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.models.users import User
from ai_news_bot.web.api.news_task.schema import (
    NewsTaskCreateSchema,
    NewsTaskUpdateSchema,
    RSSItemSchema,
)


@pytest.mark.anyio
async def test_news_task_endpoints(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Tests news task creation."""
    url = fastapi_app.url_path_for("create_news_task")
    payload = NewsTaskCreateSchema(
        title="Test Task",
        description="This is a test task",
        end_date=(datetime.now() + timedelta(days=7)),
    )
    response = await client.post(
        url,
        json=payload.model_dump(mode="json"),
        headers={"Content-Type": "application/json", **auth_headers},
    )
    assert response.status_code == 200
    assert response.json()["title"] == payload.title
    # Test updates
    updated_payload = NewsTaskUpdateSchema(
        title="Updated Test Task",
        description="This is an updated test task",
        end_date=(datetime.now() + timedelta(days=5)),
        is_active=True,
        relevant_news=["News one", "News two"],
        non_relevant_news=["News three", "News four"],
    )
    update_url = fastapi_app.url_path_for(
        "update_news_task",
        task_id=response.json()["id"],
    )
    update_response = await client.put(
        update_url,
        json=updated_payload.model_dump(mode="json"),
        headers={"Content-Type": "application/json", **auth_headers},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == updated_payload.title
    assert update_response.json()["relevant_news"] == (
        updated_payload.relevant_news
    )
    wrong_id_url = fastapi_app.url_path_for("update_news_task", task_id=99999)
    wrong_id_response = await client.put(
        wrong_id_url,
        json=updated_payload.model_dump(mode="json"),
        headers={"Content-Type": "application/json", **auth_headers},
    )
    assert wrong_id_response.status_code == 404


@pytest.mark.anyio
async def test_news_crud(dbsession: AsyncSession, test_user: str) -> None:
    user = await dbsession.get(User, test_user)
    new_task = NewsTaskCreateSchema(
        title="CRUD Test Task",
        description="This is a test task",
        end_date=(datetime.now() + timedelta(days=7)),
    )
    created_task = await news_task_crud.create(
        session=dbsession,
        obj_in=new_task,
        user=user,
    )
    assert created_task.title == new_task.title
    edited_task = await news_task_crud.update(
        session=dbsession,
        obj_id=created_task.id,
        obj_in=NewsTaskCreateSchema(
            title="Updated Task Title",
            description="Updated task description",
            end_date=(datetime.now() + timedelta(days=5)),
        ),
    )
    assert edited_task.title == "Updated Task Title"
    # Test adding and retrieveing a false positive
    false_positive = RSSItemSchema(
        title="False Positive",
        link="http://example.com/false-positive",
        description="This is a false positive news item.",
        pub_date=datetime.now(),
        source_name="Example Source",
    )
    updated_task = await news_task_crud.add_false_positive(
        news=false_positive,
        news_task_id=created_task.id,
        session=dbsession,
    )
    retrieved_false_positives = await news_task_crud.get_false_positives(
        news_task_id=created_task.id,
        session=dbsession,
    )
    assert len(updated_task.false_positives) == 1
    assert retrieved_false_positives[0].title == false_positive.title


@pytest.mark.anyio
async def test_ai_results_endpoint(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
    test_user: str,
) -> None:
    """Tests AI results endpoint."""
    user = await dbsession.get(User, test_user)
    new_task = NewsTaskCreateSchema(
        title="AI Results Test Task",
        description="This is a test task for AI results",
        end_date=(datetime.now() + timedelta(days=7)),
    )
    created_task = await news_task_crud.create(
        session=dbsession,
        obj_in=new_task,
        user=user,
    )
    url = fastapi_app.url_path_for(
        "check_ai_news_task",
    )
    payload = {
        "news_task_id": created_task.id,
        "news_item": "This is a test news item to be evaluated by AI."
    }

    # Mock the process_news function to avoid OpenAI API calls
    patch_target = "ai_news_bot.web.api.news_task.views.process_news"
    with mock.patch(patch_target) as mock_process:
        mock_process.return_value = True

        response = await client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json", **auth_headers},
        )

        # Verify the mock was called with correct parameters
        mock_process.assert_called_once()
        call_args = mock_process.call_args
        assert call_args[1]["news"] == payload["news_item"]
        assert call_args[1]["news_task"] == created_task
        assert "initial_prompt" in call_args[1]
        assert "deepseek_api_key" in call_args[1]

    assert response.status_code == 200
    assert response.json() is True


@pytest.mark.anyio
async def test_add_sources_to_news_task(
    dbsession: AsyncSession,
    test_user: str,
) -> None:
    """Test adding RSS and Telegram sources to a news task."""
    user = await dbsession.get(User, test_user)

    # Create a new task
    new_task = NewsTaskCreateSchema(
        title="Sources Test Task",
        description="This is a test task for sources",
        end_date=(datetime.now() + timedelta(days=7)),
    )
    created_task = await news_task_crud.create(
        session=dbsession,
        obj_in=new_task,
        user=user,
    )

    # Verify initial state - empty sources
    assert created_task.rss_urls == {}
    assert created_task.tg_urls == {}

    # Add RSS sources
    rss_sources = {
        "TechCrunch": "https://techcrunch.com/feed/",
        "HackerNews": "https://news.ycombinator.com/rss",
    }
    created_task.rss_urls = rss_sources
    await dbsession.commit()
    await dbsession.refresh(created_task)

    assert created_task.rss_urls == rss_sources
    assert len(created_task.rss_urls) == 2

    # Add Telegram sources
    tg_sources = {
        "TechNews": "https://t.me/technews",
        "DevChannel": "https://t.me/devchannel",
    }
    created_task.tg_urls = tg_sources
    await dbsession.commit()
    await dbsession.refresh(created_task)

    assert created_task.tg_urls == tg_sources
    assert len(created_task.tg_urls) == 2

    # Verify both sources are persisted
    retrieved_task = await news_task_crud.get_object_by_id(
        session=dbsession,
        obj_id=created_task.id,
    )
    assert retrieved_task.rss_urls == rss_sources
    assert retrieved_task.tg_urls == tg_sources
