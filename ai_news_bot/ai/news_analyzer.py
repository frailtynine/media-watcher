import asyncio
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import httpx
from fastapi import FastAPI
from openai import AsyncOpenAI
from rss_parser import RSSParser

from ai_news_bot.ai.prompts import Prompts
from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.crud.events import crud_event
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.settings import settings
from ai_news_bot.telegram.bot import queue_task_message
from ai_news_bot.web.api.news_task.schema import RSSItemSchema

if TYPE_CHECKING:
    from ai_news_bot.db.models.events import Event

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

RSS_URL = "https://tass.ru/rss/v2.xml"


def get_news(
    response: httpx.Response,
    processed_news_links: set[str],
) -> tuple[set[str], list[RSSItemSchema]]:
    """
    Fetches news items from the RSS feed.

    :return: List of news items.
    """
    rss_feed = RSSParser.parse(response.text)
    rss_list = [
        RSSItemSchema(
            title=item.title.content,
            link=item.links[0].content,
            description=item.description.content if item.description else "",
            pub_date=datetime.strptime(
                item.pub_date.content,
                "%a, %d %b %Y %H:%M:%S %z",
            ),
        )
        for item in rss_feed.channel.items
    ]
    one_hour_ago = datetime.now() - timedelta(hours=1)
    rss_list = [
        item for item in rss_list
        if item.pub_date.replace(tzinfo=None) > one_hour_ago
    ]
    rss_list = rss_list[:50]
    news_to_process = []
    for item in rss_list:
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
    event: "Event",
    initial_prompt: str,
) -> bool:
    async with AsyncOpenAI(
        api_key=settings.deepseek,
        base_url="https://api.deepseek.com",
        timeout=5.0,
    ) as client:
        false_positives = "\n".join(
            f"- {item['title']} \n\n {item['description']}"
            for item in event.false_positives
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
                            f"Market: {event.title} \n\n"
                            f" {event.rules}"
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


async def compose_post(
    news: RSSItemSchema,
    event: "Event",
) -> str:
    """
    Composes a post for the given news item and event.
    :return: Post text.
    """
    positives = "\n".join(
        f"- {item['title']} \n\n {item['description']}"
        for item in event.positives
    )
    async with AsyncOpenAI(
        api_key=settings.deepseek,
        base_url="https://api.deepseek.com",
        timeout=50.0,
    ) as client:
        try:
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": Prompts.SUGGEST_POST,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"News: {news.title} \n {news.description} \n\n"
                            f"Market: {event.title} \n\n"
                            f"{event.rules}\n\n"
                            f"Link: {event.link}\n\n"
                            f"Previous relevant news: {positives}"
                        ),
                    },
                ],
            )
            logger.info(
                f"Composed post: {response.choices[0].message.content}",
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error composing post: {e}")
            return "Error composing post, please check logs."


async def news_analyzer(app: FastAPI) -> None:
    processed_news_links: set[str] = set()
    while True:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("Fetching RSS feed...")
            try:
                rss_response = await client.get(RSS_URL)
            except Exception as e:
                logger.error(f"Error fetching RSS feed: {e}")
                await asyncio.sleep(60)
                continue
            logger.info(f"Fetched RSS feed, {rss_response.status_code}")
        processed_news_links, news_to_process = get_news(
            response=rss_response,
            processed_news_links=processed_news_links,
        )
        logger.info(f"Current news count in queue: {len(news_to_process)}")
        if not news_to_process:
            logger.info("No news to process, sleeping for 60 seconds.")
            await asyncio.sleep(60)
            continue
        async with get_standalone_session() as session:
            tasks: list[Event] = await crud_event.get_active_tasks(
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
            for news in news_to_process:
                for task in tasks:
                    logger.info(
                        f"Processing news: {news.title} "
                        f"for task: {task.title}"
                    )
                    try:
                        is_relevant = await asyncio.wait_for(
                            process_news(
                                news=news,
                                event=task,
                                initial_prompt=Prompts.ROLE,
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
                            await crud_event.add_positive(
                                    news=news,
                                    event_id=task.id,
                                    session=session,
                                )
                        except Exception as e:
                            logger.error(f"Error adding positive event: {e}")
                        try:
                            post_text = await compose_post(news, task)
                            logger.info(f"Composed post: {post_text}")
                        except asyncio.TimeoutError:
                            logger.error(
                                f"Composing post for news {news.title} "
                                f"and task {task.title} timed out.",
                            )
                            post_text = "Error composing post."
                        description_text = (
                            f"{news.description}\n\n"
                            if news.description
                            else ""
                        )
                        for chat_id in chat_ids:
                            await queue_task_message(
                                chat_id=chat_id,
                                text=(
                                    f"News: [{news.title}]({news.link})\n"
                                    f"{description_text}"
                                    f"Market: [{task.title}]({task.link})\n\n"
                                    f"Post suggestion: {post_text}"
                                ),
                                task_id=str(task.id),
                            )
        await asyncio.sleep(60)
