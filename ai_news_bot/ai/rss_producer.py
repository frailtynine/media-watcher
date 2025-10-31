import logging
import asyncio
import httpx

from ai_news_bot.ai.utils import (
    parse_rss_feed,
    get_rss_feed,
    add_news_to_db,
    get_sources
)


logger = logging.getLogger(__name__)


async def rss_producer():
    logger.info("Starting RSS producer...")
    tasks = []
    rss_urls = await get_sources(rss=True)
    if not rss_urls:
        logger.info("No RSS URLs configured.")
        return
    rss_urls_list = list(rss_urls.values())
    for url in rss_urls_list:
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
