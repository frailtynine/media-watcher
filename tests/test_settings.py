import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.settings import settings_crud
from ai_news_bot.web.api.settings.schema import (
    SettingsSchema,
    ApiSettingsSchema
)


@pytest.mark.anyio
async def test_get_settings_creates_default_when_none_exist(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test GET /settings creates default settings when none exist."""
    # Ensure no settings exist
    existing_settings = await settings_crud.get_all_objects(session=dbsession)
    for setting in existing_settings:
        await settings_crud.delete_object_by_id(
            session=dbsession, obj_id=setting.id
        )
    await dbsession.commit()

    url = fastapi_app.url_path_for("get_settings")
    response = await client.get(
        url,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "deepseek" in data


@pytest.mark.anyio
async def test_get_settings_returns_existing_settings(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test GET /settings returns existing settings."""
    # Create test settings
    await settings_crud.create(
        session=dbsession,
        obj_in=SettingsSchema(
            deepseek="test-deepseek-key",
        )
    )

    url = fastapi_app.url_path_for("get_settings")
    response = await client.get(
        url,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deepseek"] == "test-deepseek-key"


@pytest.mark.anyio
async def test_get_settings_requires_authentication(
    fastapi_app: FastAPI,
    client: AsyncClient,
) -> None:
    """Test GET /settings requires authentication."""
    url = fastapi_app.url_path_for("get_settings")
    response = await client.get(url)

    assert response.status_code == 401


@pytest.mark.anyio
async def test_update_settings_creates_new_when_none_exist(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test PUT /settings creates new settings when none exist."""
    # Ensure no settings exist
    existing_settings = await settings_crud.get_all_objects(session=dbsession)
    for setting in existing_settings:
        await settings_crud.delete_object_by_id(
            session=dbsession, obj_id=setting.id
        )
    await dbsession.commit()

    url = fastapi_app.url_path_for("update_settings")
    payload = ApiSettingsSchema(
        deepseek="new-deepseek-key",
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json", **auth_headers},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deepseek"] == "new-deepseek-key"


@pytest.mark.anyio
async def test_update_settings_updates_existing_settings(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test PUT /settings updates existing settings."""
    # Create initial settings
    initial_settings = await settings_crud.create(
        session=dbsession,
        obj_in=ApiSettingsSchema(
            deepseek="old-deepseek-key",
        )
    )

    url = fastapi_app.url_path_for("update_settings")
    payload = ApiSettingsSchema(
        deepseek="updated-deepseek-key",
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json", **auth_headers},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deepseek"] == "updated-deepseek-key"

    # Verify the settings were actually updated in the database
    updated_settings = await settings_crud.get_object_by_id(
        session=dbsession, obj_id=initial_settings.id
    )
    assert updated_settings.deepseek == "updated-deepseek-key"


@pytest.mark.anyio
async def test_update_settings_with_null_keys(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test PUT /settings with null API keys."""
    url = fastapi_app.url_path_for("update_settings")
    payload = ApiSettingsSchema(
        deepseek=None,
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json", **auth_headers},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deepseek"] is None


@pytest.mark.anyio
async def test_update_settings_requires_authentication(
    fastapi_app: FastAPI,
    client: AsyncClient,
) -> None:
    """Test PUT /settings requires authentication."""
    url = fastapi_app.url_path_for("update_settings")
    payload = ApiSettingsSchema(
        deepseek="test",
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 401
