import pytest
from unittest.mock import patch, MagicMock

from ai_news_bot.web.api.settings.validators import (
    validate_telegram_channel_url
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
