import httpx
import logging
from typing import Union
from dateutil.parser import parse as parse_date
from pydantic import BaseModel

from newspaper import Article
from openai import AsyncOpenAI
from rss_parser import RSSParser

from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.web.api.news_task.schema import RSSItemSchema
from ai_news_bot.db.crud.news import crud_news
from ai_news_bot.db.crud.settings import settings_crud


logger = logging.getLogger(__name__)

# TODO: Use only with admin API key
# async def check_balance():
#     async with get_standalone_session() as session:
#         user_settings = await settings_crud.get_all_objects(session=session)
#         if not user_settings or not user_settings[0].deepseek:
#             logger.warning("DeepSeek API key not found in settings.")
#             return
#         api_key = user_settings[0].deepseek
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             "https://api.openai.com/v1/organization/costs",
#             headers={"Authorization": f"Bearer {api_key}"},
#         )
#         if response.status_code == 200:
#             res_json = response.json()
#             balance = res_json["data"][0]["results"][0]["amount"]["value"]
#             if float(balance) < 1:
#                 await send_deepseek_balance_alert(balance=balance)
#                 logger.warning(
#                     f"DeepSeek balance is low: ${balance:.2f}"
#                 )
#         else:
#             logger.error(
#                 f"Failed to retrieve balance: {response.status_code}"
#             )


class TranslateResponseSchema(BaseModel):
    title: str
    description: str | None


async def send_deepseek_balance_alert(
    zero_balance: bool = False, balance: float | None = None
):
    from ai_news_bot.telegram.bot import queue_task_message
    async with get_standalone_session() as session:
        chat_ids = await telegram_user_crud.get_all_chat_ids(session=session)
        text_zero_balance = (
            "⚠️ Alert: Your DeepSeek balance is zero. "
            "Please top up to ensure uninterrupted service."
        )
        text_low_balance = (
            f"⚠️ Alert: Your DeepSeek balance is low (${balance:.2f}). "
            "Please top up to ensure uninterrupted service."
        )
        for chat_id in chat_ids:
            await queue_task_message(
                chat_id=chat_id,
                text=text_zero_balance if zero_balance else text_low_balance,
            )


def get_full_text(url: str) -> Article | None:
    """Fetch the full text of an article from a URL."""
    article = Article(url, fetch_images=False)
    try:
        article.download()
        article.parse()
        return article
    except Exception as e:
        logger.error(f"Error fetching full text from {url}: {e}")
        return None


def prepare_translated_response(
    response: TranslateResponseSchema | None,
    origin_text: Union[RSSItemSchema, Article],
) -> str:
    """Prepare translated text from TranslateResponseSchema."""
    link = (
        origin_text.link if hasattr(origin_text, 'link')
        else origin_text.url
    )
    if not response:
        title_line = f"[{origin_text.title}]({link})\n\n"
        if hasattr(origin_text, "description"):
            body = origin_text.description
        else:
            body = origin_text.text
        return (
            f"{title_line}{body}\n\n"
            "Перевод не случился, сорян."
        )
    translated_text = f"[{response.title}]({link})\n\n"
    if response.description:
        translated_text += f"{response.description}\n\n"
    return translated_text


async def translate_with_ai(
    text: Union[RSSItemSchema | Article],
) -> str:
    """Translate text to Russian using AI API.

    Args:
        text: RSSItemSchema or Newspaper3k Article object.
    """
    async with get_standalone_session() as session:
        settings = await settings_crud.get_all_objects(session=session)
        if settings:
            api_key = settings[0].deepseek
        else:
            logger.warning("AI API key not found in settings.")
            return text
    if type(text) is RSSItemSchema:
        text_str = f"{text.title}\n\n{text.description}"
    else:
        text_str = f"{text.title}\n\n{text.text}"
    try:
        async with AsyncOpenAI(
            api_key=api_key,
            timeout=120.0,
            max_retries=5,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        ) as client:
            response = await client.beta.chat.completions.parse(
                model="gemini-2.5-flash-lite",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Translate to Russian and extract translated text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Translate the following text to Russian: \n\n"
                            f"{text_str}"
                        ),
                    },
                ],
                response_format=TranslateResponseSchema
            )
            return prepare_translated_response(
                response=response.choices[0].message.parsed,
                origin_text=text,
            )
    except Exception as e:
        logger.error(f"AI translation error: {e}")
        return prepare_translated_response(response=None, origin_text=text)


def parse_rss_feed(response: httpx.Response) -> list[RSSItemSchema]:
    """
    Parse RSS feed response and return list of RSSItemSchema.

    Args:
        response: httpx.Response object containing RSS feed XML.
    """
    if response.status_code == 200:
        try:
            feed = RSSParser.parse(response.text)
        except Exception as e:
            logger.warning(f"Failed to parse RSS feed: {e}, {response.url}")
    else:
        logger.warning(
            f"Bad response status: {response.status_code}, {response.url}"
        )
    messages = [
        RSSItemSchema(
            title=item.title.content,
            link=item.links[0].content,
            description=(
                item.description.content if item.description else ""
            ),
            pub_date=parse_date(item.pub_date.content),
        )
        for item in feed.channel.items
    ]
    return messages


async def get_rss_feed(url: str) -> httpx.Response:
    """Fetch RSS feed from a URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response


async def add_news_to_db(
    news_items: list[RSSItemSchema],
) -> None:
    """
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


async def get_sources(
    rss: bool = False,
    telegram: bool = False
) -> dict[str, str]:
    """
    Retrieve RSS or Telegram sources from settings.

    Args:
        rss: If True, retrieve RSS sources.
        telegram: If True, retrieve Telegram sources.
    """
    async with get_standalone_session() as session:
        settings = await settings_crud.get_all_objects(session=session)
        if settings and telegram:
            return settings[0].tg_urls
        elif settings and rss:
            return settings[0].rss_urls
        return {}
