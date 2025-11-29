import pytest
from unittest.mock import patch

from ai_news_bot.web.api.news_task.validators import (
    validate_telegram_channel_url,
    normalize_telegram_url
)


@pytest.mark.anyio
async def test_validate_telegram_channel_url():
    """Test validate_telegram_channel_url with mocked Telethon client."""
    valid_url = "https://t.me/astrapress"
    valid_url_alt = "t.me/astrapress/"

    from ai_news_bot.web.api.news_task.schema import RSSItemSchema
    from datetime import datetime, timezone

    # Mock successful message fetching
    mock_messages = [
        RSSItemSchema(
            title="Test message",
            description="Test description",
            link="https://t.me/astrapress/1",
            pub_date=datetime.now(timezone.utc),
            source_name="astrapress",
        )
    ]

    with patch(
        "ai_news_bot.web.api.news_task.validators."
        "get_messages_from_telegram_channel"
    ) as mock_get_messages:
        # Test valid Telegram URL - should return messages
        mock_get_messages.return_value = mock_messages
        is_valid, result_url = await validate_telegram_channel_url(valid_url)
        assert is_valid is True
        assert result_url == valid_url
        mock_get_messages.assert_called_with(valid_url, 1)

        # Test alternative valid format - should normalize and validate
        mock_get_messages.return_value = mock_messages
        is_valid, result_url = await validate_telegram_channel_url(
            valid_url_alt
        )
        assert is_valid is True
        assert result_url == "https://t.me/astrapress/"
        mock_get_messages.assert_called_with("https://t.me/astrapress/", 1)

        # Test channel returns no messages
        mock_get_messages.return_value = []
        is_valid, error_msg = await validate_telegram_channel_url(valid_url)
        assert is_valid is False
        assert "недоступен" in error_msg

        # Test exception handling
        mock_get_messages.side_effect = Exception("Connection error")
        is_valid, error_msg = await validate_telegram_channel_url(valid_url)
        assert is_valid is False
        assert "Что-то не такя" in error_msg


def test_normalize_telegram_url():
    """Test normalize_telegram_url function with various input formats."""

    # Test already normalized URL (should remain unchanged)
    assert normalize_telegram_url("https://t.me/channel") == \
        "https://t.me/channel"
    assert normalize_telegram_url("https://t.me/example_channel") == \
        "https://t.me/example_channel"

    # Test t.me/ prefix removal
    assert normalize_telegram_url("t.me/channel") == "https://t.me/channel"
    assert normalize_telegram_url("t.me/example_channel") == \
        "https://t.me/example_channel"

    # Test @ prefix removal
    assert normalize_telegram_url("@channel") == "https://t.me/channel"
    assert normalize_telegram_url("@example_channel") == \
        "https://t.me/example_channel"

    # Test plain channel name
    assert normalize_telegram_url("channel") == "https://t.me/channel"
    assert normalize_telegram_url("example_channel") == \
        "https://t.me/example_channel"

    # Test leading slash removal
    assert normalize_telegram_url("/channel") == "https://t.me/channel"
    assert normalize_telegram_url("//channel") == "https://t.me/channel"

    # Test edge cases that were problematic with lstrip()
    assert normalize_telegram_url("entertainment") == \
        "https://t.me/entertainment"
    assert normalize_telegram_url("@entertainment") == \
        "https://t.me/entertainment"
    assert normalize_telegram_url("t.me/entertainment") == \
        "https://t.me/entertainment"
    assert normalize_telegram_url("example_news") == \
        "https://t.me/example_news"

    # Test mixed cases
    assert normalize_telegram_url("t.me/@channel") == \
        "https://t.me/@channel"
    assert normalize_telegram_url("@/channel") == "https://t.me/channel"

    # Test with trailing slashes
    assert normalize_telegram_url("t.me/channel/") == \
        "https://t.me/channel/"
    assert normalize_telegram_url("@channel/") == "https://t.me/channel/"
