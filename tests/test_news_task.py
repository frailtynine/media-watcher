from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.models.users import User
from ai_news_bot.web.api.news_task.schema import (
    NewsTaskCreateSchema,
    RSSItemSchema
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
    updated_payload = NewsTaskCreateSchema(
        title="Updated Test Task",
        description="This is an updated test task",
        end_date=(datetime.now() + timedelta(days=5)),
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
    wrong_id_url = fastapi_app.url_path_for("update_news_task", task_id=99999)
    wrong_id_response = await client.put(
        wrong_id_url,
        json=updated_payload.model_dump(mode="json"),
        headers={"Content-Type": "application/json", **auth_headers},
    )
    assert wrong_id_response.status_code == 404


@pytest.mark.anyio
async def test_news_crud(dbsession: AsyncSession, test_user: str):
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
