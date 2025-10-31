import asyncio
import httpx
import logging

from ai_news_bot.web.api.news_task.schema import RSSItemSchema
from ai_news_bot.ai.utils import (
    parse_rss_feed,
    get_sources,
    add_news_to_db
)


logger = logging.getLogger(__name__)


RSS_HUB_HOSTS = [
    "rsshub.umzzz.com",
    "rss.owo.nz",
    "rsshub.ktachibana.party",
    "rsshub.isrss.com",
    "rsshub.asailor.org"
]


async def fetch_rss_feed(channel_url: str) -> httpx.Response | None:
    channel_name = channel_url.replace("https://t.me/", "").rstrip("/")
    async with httpx.AsyncClient() as client:
        for host in RSS_HUB_HOSTS:
            url = f"https://{host}/telegram/channel/{channel_name}/showLinkPreview=0&showViaBot=0&showReplyTo=0&showFwdFrom=0&showFwdFromAuthor=0&showInlineButtons=0&showMediaTagInTitle=1&showMediaTagAsEmoji=1&includeFwd=0&includeReply=1&includeServiceMsg=0&includeUnsupportedMsg=0" # noqa
            response = await client.get(url)
            if response.status_code == 200:
                return response
        logger.error(f"All RSSHub hosts failed for channel: {channel_url}")


async def fetch_and_parse_telegram_channels(
    channel_urls: list[str],
) -> list[RSSItemSchema]:
    tasks = []
    for channel_url in channel_urls:
        tasks.append(fetch_rss_feed(channel_url))
    try:
        responses = await asyncio.gather(
            *tasks, return_exceptions=True
        )
        messages = []
        for rss_response in responses:
            if isinstance(rss_response, Exception):
                logger.error(f"Error fetching channel: {rss_response}")
                continue
            else:
                messages.extend(parse_rss_feed(rss_response))
        return messages
    except httpx.HTTPError as e:
        logger.error(f"HTTP error while fetching channel {channel_url}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


async def telegram_producer() -> None:
    logger.info("Starting Telegram producer...")
    channel_urls = await get_sources(telegram=True)
    if not channel_urls:
        logger.info("No Telegram channels configured.")
        return
    news_items = await fetch_and_parse_telegram_channels(
        channel_urls=list(channel_urls.values())
    )
    logger.info(f"Fetched {len(news_items)} news items from Telegram.")
    await add_news_to_db(news_items)
