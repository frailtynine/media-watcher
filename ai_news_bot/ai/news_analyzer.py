import asyncio
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import httpx
from fastapi import FastAPI
from openai import AsyncOpenAI
from redis.asyncio import ConnectionPool, Redis
from rss_parser import RSSParser

from ai_news_bot.ai.prompts import Prompts
from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.services.redis.schema import RedisNewsMessageSchema
from ai_news_bot.settings import settings
from ai_news_bot.telegram.bot import queue_task_message
from ai_news_bot.web.api.news_task.schema import NewsTaskRedisSchema, RSSItemSchema

if TYPE_CHECKING:
    from ai_news_bot.db.models.news_task import NewsTask

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

RSS_URL = "https://tass.ru/rss/v2.xml"


async def put_news_in_redis(
    news: RSSItemSchema,
    news_task: "NewsTask",
    app: FastAPI,
    result: bool,
) -> None:
    redis_pool: ConnectionPool = app.state.redis_pool
    if not redis_pool:
        logger.error("Redis pool is not initialized.")
        return
    news_task_schema = NewsTaskRedisSchema(
        **news_task.to_dict(),
        result=result,
    )
    message = RedisNewsMessageSchema(
        news=news,
        task=news_task_schema,
    ).model_dump_json()
    redis_client = Redis(connection_pool=redis_pool)
    async with redis_client:
        await redis_client.publish("relevant_news", message)


def get_news(
    response: httpx.Response,
    news_deque: deque[RSSItemSchema],
) -> tuple[deque[RSSItemSchema], list[RSSItemSchema]]:
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
        item for item in rss_list if item.pub_date.replace(tzinfo=None) > one_hour_ago
    ]
    rss_list = rss_list[:50]
    news_to_process = []
    for item in rss_list:
        if item not in news_deque:
            news_deque.append(item)
            news_to_process.append(item)
    news_to_process.sort(key=lambda x: x.pub_date)
    if not news_to_process:
        logger.info("No new news items to process.")
    return news_deque, news_to_process


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
                            f"Market: {news_task.title} \n\n"
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


async def compose_post(
    news: RSSItemSchema,
    news_task: "NewsTask",
) -> str:
    """
    Composes a post for the given news item and task.
    :return: Post text.
    """
    positives = "\n".join(
        f"- {item['title']} \n\n {item['description']}" for item in news_task.positives
    )
    async with AsyncOpenAI(
        api_key=settings.deepseek,
        base_url="https://api.deepseek.com",
        timeout=10.0,
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
                            f"Market: {news_task.title} \n\n"
                            f"{news_task.description}\n\n"
                            f"Link: {news_task.link}\n\n"
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
    news_deque: deque[RSSItemSchema] = deque(maxlen=500)
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
        news_deque, news_to_process = get_news(
            response=rss_response,
            news_deque=news_deque,
        )
        logger.info(f"Current news count in queue: {len(news_to_process)}")
        if not news_to_process:
            logger.info("No news to process, sleeping for 60 seconds.")
            await asyncio.sleep(60)
            continue
        async with get_standalone_session() as session:
            tasks: list[NewsTask] = await news_task_crud.get_active_tasks(
                session=session,
            )
        if not tasks:
            logger.info("No active tasks found")
            continue
        logger.info(f"Found {len(tasks)} active tasks")
        for news in news_to_process:
            for task in tasks:
                logger.info(
                    f"Processing news: {news.title} for task: {task.title}",
                )
                try:
                    is_relevant = await asyncio.wait_for(
                        process_news(
                            news=news,
                            news_task=task,
                            initial_prompt=Prompts.ROLE,
                        ),
                        timeout=10.0,
                    )
                except asyncio.TimeoutError:
                    logger.error(
                        f"Processing news {news.title} for task {task.title} "
                        "timed out.",
                    )
                    is_relevant = False
                logger.info(
                    f"Processed news: {news.title}, "
                    f"relevant to task '{task.title}': {is_relevant}",
                )
                await asyncio.wait_for(
                    put_news_in_redis(
                        news=news,
                        news_task=task,
                        app=app,
                        result=is_relevant,
                    ),
                    timeout=10.0,
                )
                if is_relevant:
                    async with get_standalone_session() as session:
                        chat_ids = await telegram_user_crud.get_all_chat_ids(
                            session=session,
                        )
                        await news_task_crud.add_positive(
                            news=news,
                            news_task_id=task.id,
                            session=session,
                        )
                    post_text = await compose_post(news, task)
                    logger.info(f"Composed post: {post_text}")
                    description_text = (
                        f"{news.description}\n\n" if news.description else ""
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
