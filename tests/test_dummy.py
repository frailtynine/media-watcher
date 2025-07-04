import uuid

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.dao.dummy_dao import DummyDAO
from ai_news_bot.db.models.dummy_model import DummyModel
from ai_news_bot.web.api.dummy.schema import DummyModelInputDTO


@pytest.mark.anyio
async def test_creation(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests dummy instance creation."""
    url = fastapi_app.url_path_for("create_dummy_model")
    test_name = uuid.uuid4().hex
    response = await client.put(url, json={"name": test_name})
    assert response.status_code == status.HTTP_200_OK
    dao = DummyDAO(dbsession)

    instances = await dao.filter(name=test_name)
    assert instances[0].name == test_name


@pytest.mark.anyio
async def test_getting(
    fastapi_app: FastAPI,
    client: AsyncClient,
    dbsession: AsyncSession,
) -> None:
    """Tests dummy instance retrieval."""
    crud = BaseCRUD(DummyModel)
    test_name = uuid.uuid4().hex
    obj_in = DummyModelInputDTO(name=test_name)
    object = await crud.create(obj_in=obj_in, session=dbsession)
    url = fastapi_app.url_path_for("get_dummy_model", dummy_id=object.id)
    response = await client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == test_name
    assert response.json()["id"] == object.id
