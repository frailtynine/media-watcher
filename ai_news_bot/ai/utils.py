import httpx
import logging

from newspaper import Article
import deepl

from ai_news_bot.settings import settings
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.db.crud.telegram import telegram_user_crud


logger = logging.getLogger(__name__)


async def check_balance():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.deepseek.com/user/balance",
            headers={"Authorization": f"Bearer {settings.deepseek}"},
        )
        if response.status_code == 200:
            response_json = response.json()
            if not response_json.get("is_available"):
                await send_deepseek_balance_alert(zero_balance=True)
                logger.warning("DeepSeek balance is zero.")
            else:
                balance = response_json["balance_infos"][0]["total_balance"]
                if balance < 1:
                    await send_deepseek_balance_alert(balance=balance)
                    logger.warning(
                        f"DeepSeek balance is low: ${balance:.2f}"
                    )
        else:
            logger.error(
                f"Failed to retrieve balance: {response.status_code}"
            )


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
    article: Article
) -> str | None:
    """Translate article text to English using DeepSeek API."""
    deepl_client = deepl.DeepLClient(settings.deepl)
    full_text = f"{article.title}\n\n{article.text}"
    response = deepl_client.translate_text(full_text, target_lang="RU")
    return response.text if response else None
