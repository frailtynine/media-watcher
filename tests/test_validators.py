import pytest
from unittest.mock import patch, MagicMock

from ai_news_bot.web.api.settings.validators import (
    validate_telegram_channel_url,
    normalize_telegram_url
)


@pytest.mark.anyio
async def test_validate_telegram_channel_url():
    """Test validate_telegram_channel_url with mocked fetch_rss_feed."""
    valid_url = "https://t.me/astrapress"
    valid_url_alt = "t.me/astrapress/"
    invalid_url = "https://example.com/some_channel"

    # Mock successful RSS feed response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<?xml version='1.0'?><rss>test content</rss>"

    with patch(
        "ai_news_bot.web.api.settings.validators.fetch_rss_feed"
    ) as mock_fetch:
        # Test valid Telegram URL - should return mock response
        mock_fetch.return_value = mock_response
        is_valid, result_url = await validate_telegram_channel_url(valid_url)
        assert is_valid is True
        assert result_url == valid_url
        mock_fetch.assert_called_with(valid_url)

        # Test alternative valid format - should normalize and return response
        mock_fetch.return_value = mock_response
        is_valid, result_url = await validate_telegram_channel_url(
            valid_url_alt
        )
        assert is_valid is True
        assert result_url == "https://t.me/astrapress/"
        mock_fetch.assert_called_with("https://t.me/astrapress/")

        # Test invalid URL - should return None (no RSS feed available)
        mock_fetch.return_value = None
        is_valid, error_msg = await validate_telegram_channel_url(invalid_url)
        assert is_valid is False
        assert "недоступен" in error_msg
        # The validator will normalize the URL by prepending https://t.me/
        expected_url = "https://t.me/https://example.com/some_channel"
        mock_fetch.assert_called_with(expected_url)


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
