import asyncio
import logging
from datetime import datetime, timezone

import httpx
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.prompt import crud_prompt
from ai_news_bot.db.crud.events import crud_event
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.settings import settings
from ai_news_bot.telegram.bot import queue_task_message
from ai_news_bot.web.api.events.schema import EventResponse


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


URL = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S %Z"
TARGET_HOURS = [
    (11, 0),  # 11:00 UTC
    (12, 0),  # 12:00 UTC
    (15, 0),  # 15:00 UTC
    (18, 30),  # 18:30 UTC
    (20, 0),  # 20:00 UTC
    (20, 30),  # 20:30 UTC
    (21, 0),  # 21:00 UTC
]


def should_run_ai_check() -> bool:
    """Check if current UTC time matches any of the target hours."""
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    current_minute = now.minute

    return (current_hour, current_minute) in TARGET_HOURS


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
            crypto_data["quote"]["USD"]["last_updated"].replace("Z", "+00:00"),
        )
        result.append((slug, price, timestamp))
    return result


async def send_crypto_message(text: str) -> None:
    """Send a cryptocurrency update message to a Telegram chat."""
    async with get_standalone_session() as session:
        chat_ids = await telegram_user_crud.get_all_chat_ids(session=session)
        logger.info(f"Sending crypto message to {len(chat_ids)} chats.")
        for chat_id in chat_ids:
            try:
                await queue_task_message(chat_id=chat_id, text=text)
            except Exception as e:
                logger.error(f"Failed to send message to chat {chat_id}: {e}")


async def get_crypto_events(
    session: AsyncSession,
    tickers: list[str],
) -> list[EventResponse]:
    """
    Finds crypto events for a given ticker.

    Args:
        session (AsyncSession): The database session.
        tickers (list[str]): The cryptocurrency ticker symbols to check.

    Returns:
        list: A list of active crypto events for the given tickers.
    """
    events = await crud_event.get_all_objects(
        session=session,
    )
    tickers.extend(["ton", "eth", "doge", "btc", "sol"])
    crypto_events = []
    for event in events:
        if any(ticker.lower() in event.title.lower() for ticker in tickers):
            crypto_events.append(EventResponse.model_validate(event))
    return crypto_events


async def check_crypto_events_with_ai(
    event: EventResponse,
    results: list[tuple[str, float, datetime]],
):
    async with AsyncOpenAI(
        api_key=settings.deepseek,
        base_url="https://api.deepseek.com",
    ) as client:
        async with get_standalone_session() as session:
            prompt = await crud_prompt.get_or_create(
                session=session
            )
        role = prompt.crypto_role
        crypto_prices = "\n".join(
            f"{slug.capitalize()}: ${price:.4f} at "
            f"{timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}"
            for slug, price, timestamp in results
        )
        link = (
            f"https://t.me/ft_rm_bot/futurum?"
            f"startapp=event_{event.id}=source_futurumTg"
        )
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        try:
            response = await client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": role},
                    {
                        "role": "user",
                        "content": (
                            f"Here is the market title and description:\n"
                            f"Title: {event.title}\n"
                            f"Description: {event.description}\n\n"
                            f"Link: {link}.\n"
                            f"Here are the current crypto prices:\n"
                            f"{crypto_prices}\n\n"
                            f"Current time is "
                            f"{date} UTC.\n"
                        ),
                    },
                ],
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return
        answer = response.choices[0].message.content
        if answer.lower() == "false":
            logger.info(f"No action needed for event {event.id}")
            return
        else:
            logger.info(f"Action suggested for event {event.id}:{answer}")
            await send_crypto_message(
                text=answer,
            )


async def crypto_cron_job(tickers: list[str]) -> None:
    try:
        results = await get_crypto_price(tickers=tickers)
        main_crypto_report = ""
        for slug, price, timestamp in results:
            main_crypto_report += (
                f"{slug.capitalize()} is ${price:.4f}.\n"
                f"at {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"
            )
        await send_crypto_message(
            text=main_crypto_report,
        )
        async with get_standalone_session() as session:
            events = await get_crypto_events(session=session, tickers=tickers)
            logger.info(f"Found {len(events)} crypto events to check.")
        if should_run_ai_check():
            tasks = [
                check_crypto_events_with_ai(event, results)
                for event in events
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print(f"Error fetching crypto price: {e}")
        return


async def crypto_hourly_job() -> None:
    await crypto_cron_job(
        tickers=["bitcoin", "toncoin", "ethereum", "dogecoin", "solana"],
    )
