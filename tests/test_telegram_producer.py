import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.ai.telegram_producer import (
    fetch_rss_feed,
    fetch_and_parse_telegram_channels,
    add_news_to_db,
    telegram_producer,
)
from ai_news_bot.web.api.news_task.schema import RSSItemSchema


@pytest.mark.anyio
async def test_fetch_rss_feed_success():
    """Test successful RSS feed fetching from Telegram channel."""
    mock_response = MagicMock()
    mock_response.text = "<?xml version='1.0'?><rss>test content</rss>"
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        result = await fetch_rss_feed("test_channel")

        assert result == mock_response
        mock_get = mock_client.return_value.__aenter__.return_value.get
        mock_get.assert_called_once()
        # Verify the correct URL is constructed
        expected_url = (
            "https://rss.owo.nz/telegram/channel/test_channel/"
            "showLinkPreview=0&showViaBot=0&showReplyTo=0&showFwdFrom=0"
            "&showFwdFromAuthor=0&showInlineButtons=0&showMediaTagInTitle=1"
            "&showMediaTagAsEmoji=1&includeFwd=0&includeReply=1"
            "&includeServiceMsg=0&includeUnsupportedMsg=0"
        )
        mock_get.assert_called_with(expected_url)


@pytest.mark.anyio
async def test_fetch_rss_feed_http_error():
    """Test HTTP error handling in RSS feed fetching."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404", request=None, response=None
            )
        )

        with pytest.raises(httpx.HTTPStatusError):
            await fetch_rss_feed("test_channel")


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
                channel_names=["channel1", "channel2"]
            )
            
            assert len(result) == 2  # Two channels, one message each
            assert all(isinstance(item, RSSItemSchema) for item in result)
            assert mock_fetch.call_count == 2


@pytest.mark.anyio
async def test_fetch_and_parse_telegram_channels_with_exception():
    """Test handling of exceptions during channel fetching."""
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
            mock_parse.return_value = []
            
            result = await fetch_and_parse_telegram_channels(
                channel_names=["channel1", "channel2"]
            )
            
            # Should return empty list due to exception handling
            assert isinstance(result, list)


@pytest.mark.anyio
async def test_add_news_to_db(dbsession: AsyncSession):
    """Test adding news items to database."""
    news_items = [
        RSSItemSchema(
            title="Test News 1",
            description="Test description 1",
            link="https://example.com/1",
            pub_date=datetime.now()
        ),
        RSSItemSchema(
            title="Test News 2",
            description="Test description 2",
            link="https://example.com/2",
            pub_date=datetime.now()
        )
    ]
    
    with patch(
        "ai_news_bot.ai.telegram_producer.get_standalone_session"
    ) as mock_session:
        mock_session.return_value.__aenter__.return_value = dbsession
        
        # Mock the crud operations
        with patch("ai_news_bot.ai.telegram_producer.crud_news") as mock_crud:
            mock_crud.get_object_by_field = AsyncMock(return_value=None)
            mock_crud.create = AsyncMock(return_value=MagicMock())
            
            await add_news_to_db(news_items)
            
            # Verify that crud operations were called
            assert mock_crud.get_object_by_field.call_count == 2
            assert mock_crud.create.call_count == 2


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

    with patch(
        "ai_news_bot.ai.telegram_producer.fetch_and_parse_telegram_channels"
    ) as mock_fetch:
        mock_fetch.return_value = mock_news_items

        with patch(
            "ai_news_bot.ai.telegram_producer.add_news_to_db"
        ) as mock_add:
            mock_add.return_value = None

            await telegram_producer(
                channel_names=["test_channel"]
            )

            mock_fetch.assert_called_once_with(
                channel_names=["test_channel"]
            )
            mock_add.assert_called_once_with(mock_news_items)
