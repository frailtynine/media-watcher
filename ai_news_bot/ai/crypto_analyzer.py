import asyncio
from collections import deque
from datetime import datetime
from typing import TYPE_CHECKING

import httpx

from ai_news_bot.db.crud.crypto_task import crypto_task_crud
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.settings import settings
from ai_news_bot.telegram.bot import queue_task_message

if TYPE_CHECKING:
    from ai_news_bot.db.models.crypto_task import CryptoTask


URL = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"


async def get_crypto_price(ticker: str) -> float:
    """Get the current price of a cryptocurrency by its ticker."""
    api_key = settings.coinmarketcap_api_key
    if not api_key:
        raise ValueError("CoinMarketCap API key is not set in settings.")
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key,
    }
    params = {"slug": ticker, "convert": "USD"}
    async with httpx.AsyncClient() as client:
        response = await client.get(URL, headers=headers, params=params)
        data = response.json()
        crypto_id = next(iter(data["data"]))
        return data["data"][crypto_id]["quote"]["USD"]["price"]


async def crypto_analyzer():
    """Analyze cryptocurrency tasks and send updates."""
    processed_tasks = deque(maxlen=100)
    while True:
        async with get_standalone_session() as session:
            crypto_tasks: list["CryptoTask"] = await crypto_task_crud.get_active_tasks(
                session=session,
            )
            for task in crypto_tasks:
                current_minute = datetime.now().replace(microsecond=0, second=0)
                processed_task_key = f"{task.id}_{current_minute}"
                if (
                    task.measurement_time == current_minute
                    and processed_task_key not in processed_tasks
                ):
                    price = await get_crypto_price(ticker=task.ticker)
                    chat_ids = await telegram_user_crud.get_all_chat_ids(
                        session=session,
                    )
                    for chat_id in chat_ids:
                        await queue_task_message(
                            chat_id=chat_id,
                            text=(
                                f"Crypto Task Update:\n"
                                f"The price of {task.ticker}: ${price:.2f}.\n"
                                f"Market: {task.title}\n"
                                f"Description: {task.description}\n\n"
                                f"End Point: ${task.end_point}\n"
                            ),
                            task_id=str(task.id),
                        )
                    processed_tasks.append(processed_task_key)
        await asyncio.sleep(1)
