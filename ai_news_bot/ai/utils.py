import httpx
import logging
from dateutil.parser import parse as parse_date

from newspaper import Article
import deepl
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


def translate_article(
    article: Article,
    deepl_api_key: str
) -> str | None:
    """
    Translate article text to English using Deepl API.
    Use for long articles. For short texts use translate_with_deepseek.

    Args:
        article: Newspaper3k Article object with title and text.
    """
    deepl_client = deepl.DeepLClient(deepl_api_key)
    full_text = f"{article.title}\n\n{article.text}"
    response = deepl_client.translate_text(full_text, target_lang="RU")
    return response.text if response else None


async def translate_with_deepseek(
    text: str,
) -> str:
    """Translate text to Russian using AI API."""
    async with get_standalone_session() as session:
        settings = await settings_crud.get_all_objects(session=session)
        if settings:
            deepseek_api_key = settings[0].deepseek
        else:
            logger.warning("AI API key not found in settings.")
            return text
    try:
        async with AsyncOpenAI(
            api_key=deepseek_api_key,
            timeout=30.0,
            max_retries=5
        ) as client:
            response = await client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that translates"
                            "markdown text to Russian. Return only "
                            "the translated text, preserve links."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Translate the following text to Russian: {text}"
                        ),
                    },
                ],
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                logger.error(
                    "DeepSeek translation failed or returned empty content."
                )
                return text
    except Exception as e:
        logger.error(f"DeepSeek translation error: {e}")
        return text


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
            logger.warning(f"Failed to parse RSS feed: {e}")
    else:
        logger.warning(
            f"Bad response status: {response.status_code}"
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
