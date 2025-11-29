import httpx
import logging
from typing import Union
from dateutil.parser import parse as parse_date
from pydantic import BaseModel

from newspaper import Article
from openai import AsyncOpenAI
from rss_parser import RSSParser

from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.web.api.news_task.schema import RSSItemSchema
from ai_news_bot.db.crud.news import crud_news
from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.crud.settings import settings_crud


logger = logging.getLogger(__name__)


class TranslateResponseSchema(BaseModel):
    title: str
    description: str | None


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
        title_line = f"<a href=\"{link}\">{origin_text.title}</a>\n\n"
        if hasattr(origin_text, "description"):
            body = origin_text.description
        else:
            body = origin_text.text
        return (
            f"{title_line}{body}\n\n"
            "Перевод не случился, сорян."
        )
    translated_text = f"<a href=\"{link}\">{response.title}</a>\n\n"
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


def parse_rss_feed(
    response: httpx.Response,
    source_name: str,
) -> list[RSSItemSchema]:
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
            source_name=source_name,
        )
        for item in feed.channel.items
    ]
    return messages


async def get_rss_feed(
    source_name: str,
    source_url: str,
) -> tuple[httpx.Response, str]:
    """
    Fetch RSS feed from a URL.
    Args:
        source_name: The name of the RSS source.
        source_url: The URL of the RSS feed.
    Returns:
        A tuple containing the httpx.Response object and source name.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(source_url)
        response.raise_for_status()
        return response, source_name


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
                logger.info(
                    f"Added news: {item.title} from source {item.source_name}"
                )


async def get_sources(
    rss: bool = False,
    telegram: bool = False
) -> dict[str, str]:
    """
    Retrieve RSS or Telegram sources from NewsTasks.

    Args:
        rss: If True, retrieve RSS sources.
        telegram: If True, retrieve Telegram sources.
    """
    async with get_standalone_session() as session:
        all_tasks = await news_task_crud.get_all_objects(session=session)
    result = {}
    if not all_tasks:
        return result
    for task in all_tasks:
        urls = task.tg_urls if telegram else task.rss_urls
        result.update(urls)
    return result
