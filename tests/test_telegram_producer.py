import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import httpx

from ai_news_bot.ai.telegram_producer import (
    fetch_rss_feed,
    fetch_and_parse_telegram_channels,
    telegram_producer,
)
from ai_news_bot.web.api.news_task.schema import RSSItemSchema


@pytest.mark.anyio
async def test_fetch_rss_feed_success():
    """Test successful RSS feed fetching from Telegram channel."""
    mock_response = MagicMock()
    mock_response.text = "<?xml version='1.0'?><rss>test content</rss>"
    mock_response.status_code = 200

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        result = await fetch_rss_feed("https://t.me/test_channel")

        assert result == mock_response
        mock_get = mock_client.return_value.__aenter__.return_value.get
        # Should try the first host and succeed
        expected_url = (
            "https://rsshub.umzzz.com/telegram/channel/test_channel/"
            "showLinkPreview=0&showViaBot=0&showReplyTo=0&showFwdFrom=0"
            "&showFwdFromAuthor=0&showInlineButtons=0&showMediaTagInTitle=1"
            "&showMediaTagAsEmoji=1&includeFwd=0&includeReply=1"
            "&includeServiceMsg=0&includeUnsupportedMsg=0"
        )
        mock_get.assert_called_with(expected_url)


@pytest.mark.anyio
async def test_fetch_rss_feed_all_hosts_fail():
    """Test when all RSS hub hosts fail."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        result = await fetch_rss_feed("https://t.me/test_channel")

        # Should return None when all hosts fail
        assert result is None
        # Should try all 5 hosts
        mock_get = mock_client.return_value.__aenter__.return_value.get
        assert mock_get.call_count == 5


@pytest.mark.anyio
async def test_fetch_and_parse_telegram_channels_success():
    """Test successful fetching and parsing of multiple channels."""
    mock_rss_items = [
        RSSItemSchema(
            title="Test message 1",
            description="Test description 1",
            link="https://t.me/test/123",
            pub_date=datetime.now(timezone.utc)
        )
    ]

    with patch(
        "ai_news_bot.ai.telegram_producer.fetch_rss_feed"
    ) as mock_fetch:
        mock_fetch.return_value = MagicMock()
        with patch(
            "ai_news_bot.ai.telegram_producer.parse_rss_feed"
        ) as mock_parse:
            mock_parse.return_value = mock_rss_items

            result = await fetch_and_parse_telegram_channels(
                channel_urls=["https://t.me/channel1", "https://t.me/channel2"]
            )

            assert len(result) == 2  # Two channels, one message each
            assert all(isinstance(item, RSSItemSchema) for item in result)
            assert mock_fetch.call_count == 2


@pytest.mark.anyio
async def test_fetch_and_parse_telegram_channels_with_exception():
    """Test handling of exceptions during channel fetching."""
    mock_rss_items = [
        RSSItemSchema(
            title="Test message",
            description="Test description",
            link="https://t.me/test/123",
            pub_date=datetime.now(timezone.utc)
        )
    ]

    with patch(
        "ai_news_bot.ai.telegram_producer.fetch_rss_feed"
    ) as mock_fetch:
        mock_fetch.side_effect = [
            MagicMock(),  # First channel succeeds
            httpx.HTTPError("Network error")  # Second channel fails
        ]

        with patch(
            "ai_news_bot.ai.telegram_producer.parse_rss_feed"
        ) as mock_parse:
            mock_parse.return_value = mock_rss_items

            result = await fetch_and_parse_telegram_channels(
                channel_urls=["https://t.me/channel1", "https://t.me/channel2"]
            )

            # Should return items from successful channel only
            assert isinstance(result, list)
            assert len(result) == 1  # Only first channel succeeded


@pytest.mark.anyio
async def test_fetch_rss_feed_channel_name_parsing():
    """Test proper parsing of channel names from URLs."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        # Test with trailing slash
        await fetch_rss_feed("https://t.me/astrapress/")

        # Test without trailing slash
        await fetch_rss_feed("https://t.me/astrapress")

        mock_get = mock_client.return_value.__aenter__.return_value.get

        # Both calls should use "astrapress" as channel name
        call_args = [call[0][0] for call in mock_get.call_args_list]

        # Check that both URLs contain the correct channel name
        assert "/telegram/channel/astrapress/" in call_args[0]
        assert "/telegram/channel/astrapress/" in call_args[1]
        assert call_args[0] == call_args[1]  # Both should be identical


@pytest.mark.anyio
async def test_telegram_producer_integration():
    """Test the main telegram_producer function."""
    mock_news_items = [
        RSSItemSchema(
            title="Test News",
            description="Test description",
            link="https://example.com/1",
            pub_date=datetime.now(timezone.utc)
        )
    ]

    mock_sources = {
        "astrapress": "https://t.me/astrapress",
        "test_channel": "https://t.me/test_channel"
    }

    with patch(
        "ai_news_bot.ai.telegram_producer.get_sources"
    ) as mock_get_sources:
        mock_get_sources.return_value = mock_sources

        with patch(
            "ai_news_bot.ai.telegram_producer."
            "fetch_and_parse_telegram_channels"
        ) as mock_fetch:
            mock_fetch.return_value = mock_news_items

            with patch(
                "ai_news_bot.ai.telegram_producer.add_news_to_db"
            ) as mock_add:
                mock_add.return_value = None

                await telegram_producer()

                mock_get_sources.assert_called_once_with(telegram=True)
                mock_fetch.assert_called_once_with(
                    channel_urls=list(mock_sources.values())
                )
                mock_add.assert_called_once_with(mock_news_items)


@pytest.mark.anyio
async def test_telegram_producer_no_channels():
    """Test telegram_producer when no channels are configured."""
    with patch(
        "ai_news_bot.ai.telegram_producer.get_sources"
    ) as mock_get_sources:
        mock_get_sources.return_value = {}

        with patch(
            "ai_news_bot.ai.telegram_producer."
            "fetch_and_parse_telegram_channels"
        ) as mock_fetch:
            with patch(
                "ai_news_bot.ai.telegram_producer.add_news_to_db"
            ) as mock_add:
                await telegram_producer()

                mock_get_sources.assert_called_once_with(telegram=True)
                # Should not call fetch or add when no channels configured
                mock_fetch.assert_not_called()
                mock_add.assert_not_called()
