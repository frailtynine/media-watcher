import logging
from datetime import datetime

import httpx

from ai_news_bot.db.crud.crypto_task import crypto_task_crud
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.settings import settings
from ai_news_bot.telegram.bot import queue_task_message


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


URL = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"


async def get_crypto_price(
    tickers: list[str],
) -> list[tuple[str, float, datetime]]:
    """
    Fetches the current price of specified cryptocurrencies.
    Uses CoinMarketCap API.

    Args:
        tickers (list[str]): A list of cryptocurrency slugs.

    Returns:
        list[tuple[str, float, datetime]]: A list of tuples containing:
            - slug (str): The cryptocurrency slug.
            - price (float): The current price in USD.
            - last_updated (datetime): The timestamp of the last price update.

    Raises:
        ValueError: If the CoinMarketCap API key is not set in settings.
        httpx.HTTPError: If the HTTP request fails.

    Note:
        Requires the CoinMarketCap API key to be set in the variable `API`.
    """ 
    api_key = settings.coinmarketcap_api_key
    if not api_key:
        raise ValueError("CoinMarketCap API key is not set in settings.")
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key,
    }
    params = {"slug": ",".join(tickers), "convert": "USD"}
    async with httpx.AsyncClient() as client:
        response = await client.get(URL, headers=headers, params=params)
        data = response.json()
    result = []
    for crypto_data in data["data"].values():
        slug = crypto_data["slug"]
        price = crypto_data["quote"]["USD"]["price"]
        timestamp = datetime.fromisoformat(
            crypto_data["quote"]["USD"]["last_updated"].replace("Z", "+00:00")
        )
        result.append((slug, price, timestamp))
    return result


async def send_crypto_message(
    text: str
):
    """Send a cryptocurrency update message to a Telegram chat."""
    async with get_standalone_session() as session:
        chat_ids = await telegram_user_crud.get_all_chat_ids(session=session)
        logger.info(f"Sending crypto message to {len(chat_ids)} chats.")
        for chat_id in chat_ids:
            try:
                await queue_task_message(
                    chat_id=chat_id,
                    text=text,
                    task_id="0"
                )
            except Exception as e:
                logger.error(f"Failed to send message to chat {chat_id}: {e}")


async def crypto_check_price_from_db(ticker: str, price: float):
    """
    Checks active crypto tasks for a given ticker
    where the current price is within 10% of the task's
    end point.

    Args:
        ticker (str): The cryptocurrency ticker symbol to check.
        price (float): The current price of the cryptocurrency.
    Returns:
        list: A list of active tasks where the price is within 10% of the task's end point.
    Raises:
        Any exceptions raised by the database session or CRUD operations.
    """

    async with get_standalone_session() as session:
        tasks = await crypto_task_crud.get_active_tasks_by_ticker(
            session=session,
            ticker=ticker
        )
    result = []
    for task in tasks:
        if abs(price - task.end_point) / task.end_point < 0.1:
            result.append(task)
    return result


async def crypto_cron_job(tickers: list[str]):
    try:
        results = await get_crypto_price(tickers=tickers)
        for slug, price, timestamp in results:
            # Check if ticker value is close to target values from tasks
            close_tasks = await crypto_check_price_from_db(slug, price)
            if close_tasks:
                for task in close_tasks:
                    await send_crypto_message(
                        text=(
                           f"Warning! {slug} price of {price} "
                           f"is close to {task.title} task endpoint of "
                           f"{task.end_point}. End date of the "
                           f"task is {task.end_date}"
                        )
                    )
            # If no close tasks, just publish the update. 
            else:
                await send_crypto_message(
                    text=(
                        "Crypto Update:\n"
                        f"The current price of {slug} is ${price}.\n"
                        f"at {timestamp}"
                    )
                )
    except Exception as e:
        print(f"Error fetching crypto price: {e}")
        return


async def crypto_hourly_job():
    await crypto_cron_job(tickers=["bitcoin", "toncoin", "ethereum"])
