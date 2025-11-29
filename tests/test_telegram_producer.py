import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from ai_news_bot.ai.telegram_producer import (
    get_messages_from_telegram_channel,
    get_tg_client,
    telegram_producer,
)
from ai_news_bot.web.api.news_task.schema import RSSItemSchema


def create_mock_client_with_messages(messages):
    """Helper to create a mock Telegram client with specified messages."""
    mock_client = MagicMock()

    async def async_iter_messages(*args, **kwargs):
        for msg in messages:
            yield msg

    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()
    mock_client.iter_messages = MagicMock(
        return_value=async_iter_messages()
    )
    return mock_client


@pytest.mark.anyio
async def test_get_tg_client_success():
    """Test successful Telegram client creation."""
    with patch("ai_news_bot.ai.telegram_producer.settings") as mock_settings:
        mock_settings.tg_api_id = 12345
        mock_settings.tg_api_hash = "test_hash"
        mock_settings.tg_session_string = "test_session"

        with patch(
            "ai_news_bot.ai.telegram_producer.StringSession"
        ) as mock_string_session:
            with patch(
                "ai_news_bot.ai.telegram_producer.TelegramClient"
            ) as mock_client_class:
                client = get_tg_client()

                # Verify StringSession and TelegramClient were called
                mock_string_session.assert_called_once_with("test_session")
                mock_client_class.assert_called_once()
                assert client is not None


@pytest.mark.anyio
async def test_get_messages_from_telegram_channel_success():
    """Test successful message fetching from Telegram channel."""
    mock_messages = [
        MagicMock(
            id=1,
            text="Test message 1",
            raw_text="Test message 1",
            date=datetime.now(timezone.utc),
        ),
        MagicMock(
            id=2,
            text="Test message 2",
            raw_text="Test message 2",
            date=datetime.now(timezone.utc),
        ),
    ]

    with patch(
        "ai_news_bot.ai.telegram_producer.get_tg_client"
    ) as mock_get_client:
        mock_client = create_mock_client_with_messages(mock_messages)
        mock_get_client.return_value = mock_client

        result = await get_messages_from_telegram_channel(
            "test channel", "https://t.me/test_channel", limit=2
        )

        assert len(result) == 2
        assert all(isinstance(item, RSSItemSchema) for item in result)
        assert result[0].title == "Test message 1"
        assert result[0].link == "https://t.me/test_channel/1"
        assert result[1].title == "Test message 2"
        assert result[1].link == "https://t.me/test_channel/2"


@pytest.mark.anyio
async def test_get_messages_from_telegram_channel_empty():
    """Test handling of empty channel."""
    with patch(
        "ai_news_bot.ai.telegram_producer.get_tg_client"
    ) as mock_get_client:
        mock_client = create_mock_client_with_messages([])
        mock_get_client.return_value = mock_client

        result = await get_messages_from_telegram_channel(
            "empty channel", "https://t.me/empty_channel"
        )

        assert result == []


@pytest.mark.anyio
async def test_get_messages_from_telegram_channel_no_text():
    """Test filtering out messages without text."""
    mock_messages = [
        MagicMock(
            id=1,
            text=None,  # No text
            raw_text=None,
            date=datetime.now(timezone.utc),
        ),
        MagicMock(
            id=2,
            text="Valid message",
            raw_text="Valid message",
            date=datetime.now(timezone.utc),
        ),
    ]

    with patch(
        "ai_news_bot.ai.telegram_producer.get_tg_client"
    ) as mock_get_client:
        mock_client = create_mock_client_with_messages(mock_messages)
        mock_get_client.return_value = mock_client

        result = await get_messages_from_telegram_channel(
            "test channel", "https://t.me/test_channel"
        )

        # Should only return message with text
        assert len(result) == 1
        assert result[0].title == "Valid message"


@pytest.mark.anyio
async def test_telegram_producer_success():
    """Test the main telegram_producer function."""
    mock_news_items = [
        RSSItemSchema(
            title="Test News",
            description="Test description",
            link="https://t.me/channel/1",
            pub_date=datetime.now(timezone.utc),
            source_name="test channel",
        )
    ]

    mock_sources = {
        "test_channel": "https://t.me/test_channel",
        "another_channel": "https://t.me/another_channel",
    }

    with patch(
        "ai_news_bot.ai.telegram_producer.get_sources"
    ) as mock_get_sources:
        mock_get_sources.return_value = mock_sources

        with patch(
            "ai_news_bot.ai.telegram_producer."
            "get_messages_from_telegram_channel"
        ) as mock_get_messages:
            mock_get_messages.return_value = mock_news_items

            with patch(
                "ai_news_bot.ai.telegram_producer.add_news_to_db"
            ) as mock_add:
                await telegram_producer()

                mock_get_sources.assert_called_once_with(telegram=True)
                # Should be called once for each channel
                assert mock_get_messages.call_count == 2
                # Should add all collected news items
                mock_add.assert_called_once()
                added_items = mock_add.call_args[0][0]
                # Two channels, each returning mock_news_items
                assert len(added_items) == 2


@pytest.mark.anyio
async def test_telegram_producer_no_channels():
    """Test telegram_producer when no channels are configured."""
    with patch(
        "ai_news_bot.ai.telegram_producer.get_sources"
    ) as mock_get_sources:
        mock_get_sources.return_value = {}

        with patch(
            "ai_news_bot.ai.telegram_producer."
            "get_messages_from_telegram_channel"
        ) as mock_get_messages:
            with patch(
                "ai_news_bot.ai.telegram_producer.add_news_to_db"
            ) as mock_add:
                await telegram_producer()

                mock_get_sources.assert_called_once_with(telegram=True)
                # Should not fetch or add when no channels configured
                mock_get_messages.assert_not_called()
                mock_add.assert_not_called()


@pytest.mark.anyio
async def test_telegram_producer_with_exception():
    """Test telegram_producer handles exceptions gracefully."""
    mock_news_items = [
        RSSItemSchema(
            title="Test News",
            description="Test description",
            link="https://t.me/channel/1",
            pub_date=datetime.now(timezone.utc),
            source_name="test channel",
        )
    ]

    mock_sources = {
        "test_channel": "https://t.me/test_channel",
        "failing_channel": "https://t.me/failing_channel",
    }

    with patch(
        "ai_news_bot.ai.telegram_producer.get_sources"
    ) as mock_get_sources:
        mock_get_sources.return_value = mock_sources

        with patch(
            "ai_news_bot.ai.telegram_producer."
            "get_messages_from_telegram_channel"
        ) as mock_get_messages:
            # First call succeeds, second raises exception
            mock_get_messages.side_effect = [
                mock_news_items,
                Exception("Network error"),
            ]

            with patch(
                "ai_news_bot.ai.telegram_producer.add_news_to_db"
            ) as mock_add:
                await telegram_producer()

                mock_get_sources.assert_called_once_with(telegram=True)
                # Should still add successful results despite one failure
                mock_add.assert_called_once()
                added_items = mock_add.call_args[0][0]
                # Only successful channel results
                assert len(added_items) == 1


@pytest.mark.anyio
async def test_get_messages_url_parsing():
    """Test proper parsing of channel URLs."""
    test_cases = [
        ("https://t.me/channel", "channel"),
        ("https://t.me/channel/", "channel"),
        ("https://t.me/my_channel", "my_channel"),
        ("https://t.me/my_channel/", "my_channel"),
    ]

    for url, expected_channel in test_cases:
        with patch(
            "ai_news_bot.ai.telegram_producer.get_tg_client"
        ) as mock_get_client:
            mock_client = create_mock_client_with_messages([])
            mock_get_client.return_value = mock_client

            await get_messages_from_telegram_channel(
                expected_channel,
                url
            )

            # Verify iter_messages was called with correct channel name
            call_args = mock_client.iter_messages.call_args
            assert call_args[1]["entity"] == expected_channel
