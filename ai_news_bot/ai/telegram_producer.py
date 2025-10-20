import asyncio
import httpx
import logging

from ai_news_bot.db.crud.news import crud_news
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.web.api.news_task.schema import RSSItemSchema
from ai_news_bot.ai.utils import parse_rss_feed


logger = logging.getLogger(__name__)


async def fetch_rss_feed(channel_name: str) -> httpx.Response:
    url = f"https://rss.owo.nz/telegram/channel/{channel_name}/showLinkPreview=0&showViaBot=0&showReplyTo=0&showFwdFrom=0&showFwdFromAuthor=0&showInlineButtons=0&showMediaTagInTitle=1&showMediaTagAsEmoji=1&includeFwd=0&includeReply=1&includeServiceMsg=0&includeUnsupportedMsg=0" # noqa
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response


async def fetch_and_parse_telegram_channels(
    channel_names: list[str],
) -> list[RSSItemSchema]:
    tasks = []
    for channel_name in channel_names:
        tasks.append(fetch_rss_feed(channel_name))
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
        logger.error(f"HTTP error while fetching channel {channel_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


async def add_news_to_db(
    news_items: list[RSSItemSchema],
) -> None:
    """"
    Add news items to the database if they don't already exist.
    """
    async with get_standalone_session() as session:
        for item in news_items:
            existing_news = await crud_news.get_object_by_field(
                session=session, field_name="link", field_value=item.link
            )
            if not existing_news:
                await crud_news.create(session=session, obj_in=item)
                logger.info(f"Added news: {item.title}")


async def telegram_producer(
    channel_names: list[str],
):
    logger.info("Starting Telegram producer...")
    news_items = await fetch_and_parse_telegram_channels(
        channel_names=channel_names
    )
    logger.info(f"Fetched {len(news_items)} news items from Telegram.")
    await add_news_to_db(news_items)
