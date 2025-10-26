import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.settings import settings_crud
from ai_news_bot.web.api.settings.schema import SettingsSchema


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
    assert "deepl" in data
    assert "rss_urls" in data
    assert "tg_urls" in data
    assert isinstance(data["rss_urls"], dict)
    assert isinstance(data["tg_urls"], dict)


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
            deepl="test-deepl-key",
            rss_urls={"bbc": "https://feeds.bbci.co.uk/news/rss.xml"},
            tg_urls={"test_channel": "https://t.me/test"},
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
    assert data["deepl"] == "test-deepl-key"
    assert data["rss_urls"] == {"bbc": "https://feeds.bbci.co.uk/news/rss.xml"}
    assert data["tg_urls"] == {"test_channel": "https://t.me/test"}


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
    reuters_url = "https://feeds.reuters.com/reuters/topNews"
    payload = SettingsSchema(
        deepseek="new-deepseek-key",
        deepl="new-deepl-key",
        rss_urls={"reuters": reuters_url},
        tg_urls={"news_channel": "https://t.me/news"},
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json", **auth_headers},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deepseek"] == "new-deepseek-key"
    assert data["deepl"] == "new-deepl-key"
    assert data["rss_urls"] == {"reuters": reuters_url}
    assert data["tg_urls"] == {"news_channel": "https://t.me/news"}


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
        obj_in=SettingsSchema(
            deepseek="old-deepseek-key",
            deepl="old-deepl-key",
            rss_urls={"bbc": "https://feeds.bbci.co.uk/news/rss.xml"},
            tg_urls={"old_channel": "https://t.me/old"},
        )
    )

    url = fastapi_app.url_path_for("update_settings")
    payload = SettingsSchema(
        deepseek="updated-deepseek-key",
        deepl="updated-deepl-key",
        rss_urls={
            "bbc": "https://feeds.bbci.co.uk/news/rss.xml",
            "cnn": "https://rss.cnn.com/rss/edition.rss"
        },
        tg_urls={
            "new_channel": "https://t.me/new",
            "tech_channel": "https://t.me/tech"
        },
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json", **auth_headers},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deepseek"] == "updated-deepseek-key"
    assert data["deepl"] == "updated-deepl-key"
    assert data["rss_urls"]["bbc"] == "https://feeds.bbci.co.uk/news/rss.xml"
    assert data["rss_urls"]["cnn"] == "https://rss.cnn.com/rss/edition.rss"
    assert data["tg_urls"]["new_channel"] == "https://t.me/new"
    assert data["tg_urls"]["tech_channel"] == "https://t.me/tech"

    # Verify the settings were actually updated in the database
    updated_settings = await settings_crud.get_object_by_id(
        session=dbsession, obj_id=initial_settings.id
    )
    assert updated_settings.deepseek == "updated-deepseek-key"
    assert updated_settings.deepl == "updated-deepl-key"


@pytest.mark.anyio
async def test_update_settings_with_empty_dicts(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test PUT /settings with empty rss_urls and tg_urls."""
    url = fastapi_app.url_path_for("update_settings")
    payload = SettingsSchema(
        deepseek="test-key",
        deepl="test-key-2",
        rss_urls={},
        tg_urls={},
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json", **auth_headers},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rss_urls"] == {}
    assert data["tg_urls"] == {}


@pytest.mark.anyio
async def test_update_settings_with_null_keys(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test PUT /settings with null API keys."""
    url = fastapi_app.url_path_for("update_settings")
    payload = SettingsSchema(
        deepseek=None,
        deepl=None,
        rss_urls={"test": "https://example.com/rss"},
        tg_urls={"test": "https://t.me/test"},
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json", **auth_headers},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deepseek"] is None
    assert data["deepl"] is None


@pytest.mark.anyio
async def test_update_settings_requires_authentication(
    fastapi_app: FastAPI,
    client: AsyncClient,
) -> None:
    """Test PUT /settings requires authentication."""
    url = fastapi_app.url_path_for("update_settings")
    payload = SettingsSchema(
        deepseek="test",
        deepl="test",
        rss_urls={},
        tg_urls={},
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_update_settings_invalid_json_schema(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
) -> None:
    """Test PUT /settings with invalid JSON schema."""
    url = fastapi_app.url_path_for("update_settings")

    # Missing required fields
    invalid_payload = {
        "deepseek": "test-key"
        # Missing rss_urls and tg_urls
    }

    response = await client.put(
        url,
        json=invalid_payload,
        headers={"Content-Type": "application/json", **auth_headers},
    )

    assert response.status_code == 422  # Validation error
