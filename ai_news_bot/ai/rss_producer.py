import logging
import asyncio
import httpx

from ai_news_bot.ai.utils import parse_rss_feed, get_rss_feed, add_news_to_db


logger = logging.getLogger(__name__)


async def rss_producer(
    rss_urls: list[str],
):
    logger.info("Starting RSS producer...")
    tasks = []
    for url in rss_urls:
        tasks.append(get_rss_feed(url))
    try:
        responses = await asyncio.gather(
            *tasks, return_exceptions=True
        )
        messages = []
        for rss_response in responses:
            if isinstance(rss_response, Exception):
                logger.error(f"Error fetching RSS feed: {rss_response}")
                continue
            else:
                messages.extend(parse_rss_feed(rss_response))
        await add_news_to_db(messages)
        logger.info("RSS producer finished.")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error while fetching RSS feed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in RSS producer: {e}")
