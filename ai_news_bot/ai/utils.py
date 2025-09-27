from openai import AsyncOpenAI
import logging
from typing import TYPE_CHECKING

from ai_news_bot.ai.prompts import Prompts
from ai_news_bot.web.api.news_task.schema import RSSItemSchema
from ai_news_bot.settings import settings
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.db.crud.prompt import crud_prompt

if TYPE_CHECKING:
    from ai_news_bot.db.models.events import Event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


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
    async with get_standalone_session() as session:
        prompt = await crud_prompt.get_or_create(session)
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
                        "content": prompt.suggest_post,
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
