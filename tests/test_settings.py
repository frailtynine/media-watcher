import pytest
from unittest import mock
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
    payload = ApiSettingsSchema(
        deepseek="new-deepseek-key",
        deepl="new-deepl-key",
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
            deepl="old-deepl-key",
        )
    )

    url = fastapi_app.url_path_for("update_settings")
    payload = ApiSettingsSchema(
        deepseek="updated-deepseek-key",
        deepl="updated-deepl-key",
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

    # Verify the settings were actually updated in the database
    updated_settings = await settings_crud.get_object_by_id(
        session=dbsession, obj_id=initial_settings.id
    )
    assert updated_settings.deepseek == "updated-deepseek-key"
    assert updated_settings.deepl == "updated-deepl-key"


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
        deepl=None,
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
    payload = ApiSettingsSchema(
        deepseek="test",
        deepl="test",
    )

    response = await client.put(
        url,
        json=payload.model_dump(),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_add_source_rss_success(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test POST /add_source successfully adds RSS source."""
    # Ensure settings exist
    await settings_crud.create(
        session=dbsession,
        obj_in=SettingsSchema(
            deepseek=None,
            deepl=None,
            rss_urls={},
            tg_urls={},
        )
    )

    url = fastapi_app.url_path_for("add_source")

    with mock.patch(
        "ai_news_bot.web.api.settings.views.validate_rss_url"
    ) as mock_validate:
        mock_validate.return_value = (True, "https://example.com/rss.xml")
        payload = {
            "source_url": "https://example.com/rss.xml",
            "source_name": "example_news",
            "source_type": "rss"
        }

        response = await client.post(
            url,
            headers=auth_headers,
            json=payload
        )
        print(response.json())

        assert response.status_code == 200
        data = response.json()
        assert data["detail"] == "https://example.com/rss.xml"
        mock_validate.assert_called_once_with("https://example.com/rss.xml")


@pytest.mark.anyio
async def test_add_source_telegram_success(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test POST /add_source successfully adds Telegram source."""
    # Ensure settings exist
    await settings_crud.create(
        session=dbsession,
        obj_in=SettingsSchema(
            deepseek=None,
            deepl=None,
            rss_urls={},
            tg_urls={},
        )
    )

    url = fastapi_app.url_path_for("add_source")

    with mock.patch(
        "ai_news_bot.web.api.settings.views.validate_telegram_channel_url"
    ) as mock_validate:
        mock_validate.return_value = (True, "https://t.me/test_channel")
        payload = {
            "source_url": "https://t.me/test_channel",
            "source_name": "test_channel",
            "source_type": "telegram"
        }

        response = await client.post(
            url,
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["detail"] == "https://t.me/test_channel"
        mock_validate.assert_called_once_with("https://t.me/test_channel")


@pytest.mark.anyio
async def test_add_source_invalid_rss_url(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test POST /add_source with invalid RSS URL."""
    url = fastapi_app.url_path_for("add_source")

    with mock.patch(
        "ai_news_bot.web.api.settings.views.validate_rss_url"
    ) as mock_validate:
        mock_validate.return_value = (
            False, "RSS недоступен по указанному URL."
        )
        payload = {
            "source_url": "https://invalid-url.com",
            "source_name": "invalid_source",
            "source_type": "rss"
        }

        response = await client.post(
            url,
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "RSS недоступен по указанному URL." in data["detail"]


@pytest.mark.anyio
async def test_add_source_invalid_telegram_url(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test POST /add_source with invalid Telegram URL."""
    url = fastapi_app.url_path_for("add_source")

    with mock.patch(
        "ai_news_bot.web.api.settings.views.validate_telegram_channel_url"
    ) as mock_validate:
        mock_validate.return_value = (
            False, "Telegram-канал недоступен или URL неверен."
        )
        payload = {
            "source_url": "https://invalid-telegram-url.com",
            "source_name": "invalid_channel",
            "source_type": "telegram"
        }

        response = await client.post(
            url,
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        assert "Telegram-канал недоступен или URL неверен." in data["detail"]


@pytest.mark.anyio
async def test_add_source_invalid_source_type(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test POST /add_source with invalid source type."""
    url = fastapi_app.url_path_for("add_source")
    payload = {
        "source_url": "https://example.com",
        "source_name": "test_source",
        "source_type": "invalid_type"
    }

    response = await client.post(
        url,
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_add_source_crud_failure(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test POST /add_source when CRUD operation fails."""
    url = fastapi_app.url_path_for("add_source")

    with mock.patch(
        "ai_news_bot.web.api.settings.views.validate_rss_url"
    ) as mock_validate:
        mock_validate.return_value = (True, "https://example.com/rss.xml")

        with mock.patch(
            "ai_news_bot.web.api.settings.views.settings_crud."
            "add_source_to_dict"
        ) as mock_crud:
            mock_crud.return_value = None  # Simulate failure
            payload = {
                "source_url": "https://example.com/rss.xml",
                "source_name": "example_news",
                "source_type": "rss"
            }
            response = await client.post(
                url,
                json=payload,
                headers=auth_headers,
            )

            assert response.status_code == 500
            data = response.json()
            assert "Failed to add RSS source." in data["detail"]


@pytest.mark.anyio
async def test_add_source_missing_parameters(
    fastapi_app: FastAPI,
    client: AsyncClient,
    auth_headers: dict,
    dbsession: AsyncSession,
) -> None:
    """Test POST /add_source with missing required parameters."""
    url = fastapi_app.url_path_for("add_source")
    payload = {
        "source_url": "https://example.com/rss.xml",
        "source_name": "example_news"
        # Missing source_type
    }

    response = await client.post(
        url,
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422  # Validation error
