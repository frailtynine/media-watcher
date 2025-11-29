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
    for source_name, source_url in rss_urls.items():
        tasks.append(get_rss_feed(source_name, source_url))
    try:
        responses = await asyncio.gather(
            *tasks, return_exceptions=True
        )
        messages = []
        for rss_response, source_name in responses:
            if isinstance(rss_response, Exception):
                logger.error(
                    f"Error fetching RSS feed {source_name}: {rss_response}"
                )
                continue
            else:
                messages.extend(parse_rss_feed(
                    rss_response,
                    source_name
                ))
        await add_news_to_db(messages)
        logger.info("RSS producer finished.")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error while fetching RSS feed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in RSS producer: {e}")
