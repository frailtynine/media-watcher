import logging
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.crud.news import crud_news
from ai_news_bot.db.crud.prompt import crud_prompt
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.crud.settings import settings_crud
from ai_news_bot.web.api.news_task.schema import RSSItemSchema
from ai_news_bot.telegram.bot import queue_task_message

if TYPE_CHECKING:
    from ai_news_bot.db.models.news_task import NewsTask
    from ai_news_bot.db.models.news import News

logger = logging.getLogger(__name__)


async def send_news_to_telegram(news: "News", task_id: int) -> None:
    async with get_standalone_session() as session:
        chat_ids = await telegram_user_crud.get_all_chat_ids(
            session=session
        )
    for chat_id in chat_ids:
        description_text = (
            f"{news.description}\n\n"
            if news.description else ""
        )
        await queue_task_message(
            chat_id=chat_id,
            text=(
                f"News: [{news.title}]({news.link})\n"
                f"{description_text}"
            ),
            task_id=str(task_id),
            news=news,
        )


async def process_news(
    news: "News",
    news_task: "NewsTask",
    initial_prompt: str,
    deepseek_api_key: str
) -> bool:
    async with AsyncOpenAI(
        api_key=deepseek_api_key,
        timeout=15.0,
    ) as client:
        false_positives = "\n".join(
            f"- {item['title']} \n\n {item['description'][:500]}"
            for item in news_task.false_positives[-20:]
        )
        try:
            response = await client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"{initial_prompt} \n\n"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"News: {news.title} \n {news.description}. \n\n"
                            f"Filter: {news_task.title} \n\n"
                            f" {news_task.description}\n\n"
                            "Use the list of irrelevant items to "
                            "better understand what is not relevant: \n\n"
                            f"{false_positives}"
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
                    f"Unexpected response from AI: "
                    f"{response.choices[0].message.content}",
                )
                return False
        except Exception as e:
            logger.error(f"Error processing news: {e}")
            return False


async def add_positive_news(
    news_id: int,
    news_task_id: int,
) -> None:
    async with get_standalone_session() as session:
        news: "News" = await crud_news.get_object_by_id(
            session=session,
            obj_id=news_id
        )
        news_task: "NewsTask" = await news_task_crud.get_object_by_id(
            session=session,
            obj_id=news_task_id
        )
        rss_news_item = RSSItemSchema(
            title=news.title,
            link=news.link,
            description=news.description,
            pub_date=news.pub_date,
        )
        await news_task_crud.add_positive(
            news=rss_news_item,
            news_task_id=news_task.id,
            session=session,
        )


async def news_consumer() -> None:
    """Background task to process unprocessed news items."""

    async with get_standalone_session() as session:
        unprocessed_news = await crud_news.get_unprocessed_news(
            session=session
        )
        tasks: list["NewsTask"] = await news_task_crud.get_active_tasks(
            session=session,
        )
        prompt = await crud_prompt.get_or_create(
            session=session,
        )
        settings = await settings_crud.get_all_objects(session=session)
        if settings:
            deepseek_api_key = settings[0].deepseek
    if unprocessed_news:
        for news in unprocessed_news:
            try:
                logger.info(f"Processing news: {news.title}")
                no_faults = True
                for news_task in tasks:
                    try:
                        is_relevant = await process_news(
                            news=news,
                            news_task=news_task,
                            initial_prompt=prompt.role,
                            deepseek_api_key=deepseek_api_key,
                        )
                    except Exception as e:
                        logger.error(
                            f"Error processing news '{news.title}' "
                            f"for task '{news_task.title}': {e}"
                        )
                        no_faults = False
                        continue
                    if is_relevant:
                        logger.info(
                            f"News '{news.title}' is relevant for task "
                            f"'{news_task.title}'",
                        )
                        await add_positive_news(
                            news_id=news.id,
                            news_task_id=news_task.id,
                        )
                        await send_news_to_telegram(
                            news=news,
                            task_id=news_task.id,
                        )
                    else:
                        logger.info(
                            f"News '{news.title}' is not relevant for task "
                            f"'{news_task.title}'",
                        )
                # Mark news as processed after checking against all tasks
                if no_faults:
                    async with get_standalone_session() as session:
                        await crud_news.mark_news_as_processed(
                            session, news.id
                        )
            except Exception as e:
                logger.error(f"Error processing news {news.title}: {e}")
