from datetime import datetime, timedelta, timezone
import httpx
import pytest

from ai_news_bot.ai.news_analyzer import get_news


@pytest.fixture
def sample_rss_feed() -> str:
    """Provides a sample RSS feed XML."""
    now = datetime.now(timezone.utc)
    recent_pub_date = now.strftime("%a, %d %b %Y %H:%M:%S %z")
    old_pub_date = (
        now - timedelta(hours=2)
      ).strftime("%a, %d %b %Y %H:%M:%S %z")

    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Test RSS Feed</title>
  <link>http://www.example.com/</link>
  <description>This is a test RSS feed.</description>
  <item>
    <title>Recent News Item</title>
    <link>http://www.example.com/recent</link>
    <description>This is a recent news item.</description>
    <pubDate>{recent_pub_date}</pubDate>
  </item>
  <item>
    <title>Old News Item</title>
    <link>http://www.example.com/old</link>
    <description>This is an old news item.</description>
    <pubDate>{old_pub_date}</pubDate>
  </item>
  <item>
    <title>Already Processed Item</title>
    <link>http://www.example.com/processed</link>
    <description>This item was already processed.</description>
    <pubDate>{recent_pub_date}</pubDate>
  </item>
</channel>
</rss>
"""


def test_get_news_basic_functionality(sample_rss_feed: str):
    """
    Tests the basic functionality of get_news.
    - Filters out old news.
    - Filters out already processed news.
    - Returns new, recent news items.
    """
    # Arrange
    mock_response = httpx.Response(
        200,
        text=sample_rss_feed,
    )
    processed_links = {"http://www.example.com/processed"}

    # Act
    updated_links, news_to_process = get_news(
        responses=[mock_response],
        processed_news_links=processed_links,
    )

    # Assert
    assert len(news_to_process) == 1
    assert news_to_process[0].title == "Recent News Item"
    assert news_to_process[0].link == "http://www.example.com/recent"

    assert len(updated_links) == 2
    assert "http://www.example.com/recent" in updated_links
    assert "http://www.example.com/processed" in updated_links
