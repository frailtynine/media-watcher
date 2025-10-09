import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import httpx
from fastapi import FastAPI
from openai import AsyncOpenAI
from rss_parser import RSSParser

from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.crud.prompt import crud_prompt
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.settings import settings
from ai_news_bot.telegram.bot import queue_task_message
from ai_news_bot.web.api.news_task.schema import RSSItemSchema

if TYPE_CHECKING:
    from ai_news_bot.db.models.news_task import NewsTask


logger = logging.getLogger(__name__)

RSS_URLS = [
    "https://tass.ru/rss/v2.xml",
    "https://semnasem.org/rss/default.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://feeds.feedburner.com/variety/headlines",
    "https://www.kommersant.ru/rss/corp.xml",
    "https://nemoskva.net/feed/",
]


def get_news(
    responses: list[httpx.Response],
    processed_news_links: set[str],
) -> tuple[set[str], list[RSSItemSchema]]:
    """
    Fetches news items from the RSS feed.

    :return: List of news items.
    """
    rss_feeds = []
    for response in responses:
        if response.status_code == 200:
            try:
                feed = RSSParser.parse(response.text)
                rss_feeds.append(feed)
            except Exception as e:
                logger.warning(f"Failed to parse RSS feed: {e}")
        else:
            logger.warning(f"Bad response status: {response.status_code}")
    rss_lists = []
    for feed in rss_feeds:
        rss_list = [
            RSSItemSchema(
                title=item.title.content,
                link=item.links[0].content,
                description=(
                    item.description.content if item.description else ""
                ),
                pub_date=datetime.strptime(
                    item.pub_date.content,
                    "%a, %d %b %Y %H:%M:%S %z",
                ),
            )
            for item in feed.channel.items
        ]
        rss_lists.extend(rss_list)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    rss_lists = [
        item for item in rss_lists
        if item.pub_date > one_hour_ago
    ]
    news_to_process = []
    for item in rss_lists:
        if item.link not in processed_news_links:
            processed_news_links.add(item.link)
            news_to_process.append(item)
            # Prevent memory leak - keep only last 1000 links
            if len(processed_news_links) > 1000:
                # Remove 200 oldest entries (simple cleanup)
                to_remove = list(processed_news_links)[:200]
                processed_news_links -= set(to_remove)
    news_to_process.sort(key=lambda x: x.pub_date)
    if not news_to_process:
        logger.info("No new news items to process.")
    return processed_news_links, news_to_process


async def process_news(
    news: RSSItemSchema,
    news_task: "NewsTask",
    initial_prompt: str,
) -> bool:
    async with AsyncOpenAI(
        api_key=settings.deepseek,
        base_url="https://api.deepseek.com",
        timeout=5.0,
    ) as client:
        false_positives = "\n".join(
            f"- {item['title']} \n\n {item['description']}"
            for item in news_task.false_positives
        )
        try:
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"{initial_prompt} \n\n"
                            "Use the false positives list to "
                            "better understand what is not relevant: \n\n"
                            f"{false_positives}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"News: {news.title} \n {news.description}. \n\n"
                            f"Filter: {news_task.title} \n\n"
                            f" {news_task.description}"
                        ),
                    },
                ],
            )
            if (
                response.choices[0].message.content
                and response.choices[0].message.content.lower() == "true"
            ):
                return True
            elif (
                response.choices[0].message.content
                and response.choices[0].message.content.lower() == "false"
            ):
                return False
            else:
                logger.warning(
                    f"Unexpected response from Deepseek: "
                    f"{response.choices[0].message.content}",
                )
                return False
        except Exception as e:
            logger.error(f"Error processing news: {e}")
            return False


async def news_analyzer(app: FastAPI) -> None:
    logger.info("Starting news analyzer...")
    processed_news_links: set[str] = set()
    while True:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("Fetching RSS feed...")
            responses = await asyncio.gather(
                *[client.get(url) for url in RSS_URLS],
                return_exceptions=False,
            )
            logger.info(f"Fetched RSS feed with {len(responses)} responses")
        processed_news_links, news_to_process = get_news(
            responses=responses,
            processed_news_links=processed_news_links,
        )
        logger.info(f"Current news count in queue: {len(news_to_process)}")
        if not news_to_process:
            logger.info("No news to process, sleeping for 60 seconds.")
            await asyncio.sleep(60)
            continue
        async with get_standalone_session() as session:
            tasks: list["NewsTask"] = await news_task_crud.get_active_tasks(
                session=session,
            )
            chat_ids = await telegram_user_crud.get_all_chat_ids(
                session=session,
            )
        if not tasks:
            logger.info("No active tasks found")
            continue
        logger.info(f"Found {len(tasks)} active tasks")
        async with get_standalone_session() as session:
            prompt = await crud_prompt.get_or_create(
                session=session,
            )
            for news in news_to_process:
                for task in tasks:
                    logger.info(
                        (
                            f"Processing news: {news.title} "
                            f"for task: {task.title}"
                        ),
                    )
                    try:
                        is_relevant = await asyncio.wait_for(
                            process_news(
                                news=news,
                                news_task=task,
                                initial_prompt=prompt.role,
                            ),
                            timeout=10.0,
                        )
                    except asyncio.TimeoutError:
                        logger.error(
                            f"Processing news {news.title} "
                            f"for task {task.title} timed out.",
                        )
                        is_relevant = False
                    logger.info(
                        f"Processed news: {news.title}, "
                        f"relevant to task '{task.title}': {is_relevant}",
                    )
                    if is_relevant:
                        try:
                            await news_task_crud.add_positive(
                                news=news,
                                news_task_id=task.id,
                                session=session,
                            )
                        except Exception as e:
                            logger.error(f"Error adding positive news: {e}")
                        description_text = (
                            f"{news.description}\n\n"
                            if news.description else ""
                        )
                        for chat_id in chat_ids:
                            await queue_task_message(
                                chat_id=chat_id,
                                text=(
                                    f"News: [{news.title}]({news.link})\n"
                                    f"{description_text}"
                                ),
                                task_id=str(task.id),
                                news=news,
                            )
        await asyncio.sleep(60)
