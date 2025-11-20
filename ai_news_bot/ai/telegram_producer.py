from dataclasses import dataclass
import logging
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.custom.message import Message

from ai_news_bot.web.api.news_task.schema import RSSItemSchema
from ai_news_bot.ai.utils import (
    get_sources,
    add_news_to_db,
)
from ai_news_bot.settings import settings

logger = logging.getLogger(__name__)


RSS_HUB_HOSTS = [
    "rsshub.umzzz.com",
    "rss.owo.nz",
    "rsshub.ktachibana.party",
    "rsshub.isrss.com",
    "rsshub.asailor.org",
    "rsshub.rssforever.com",
    "hub.slarker.me",
    "rsshub.pseudoyu.com",
    "rsshub.ktachibana.party",
    "rsshub.asailor.org",
]


@dataclass
class TgCredentials:
    api_id: int
    api_hash: str
    session_string: str


def get_tg_client() -> TelegramClient:
    """
    Returns an authorized Telegram client.
    
    Raises ValueError if any credentials are missing.
    """
    tg_credentials = TgCredentials(
        api_id=settings.tg_api_id,
        api_hash=settings.tg_api_hash,
        session_string=settings.tg_session_string,
    )
    client = TelegramClient(
        StringSession(tg_credentials.session_string),
        tg_credentials.api_id,
        tg_credentials.api_hash,
    )
    return client


async def get_messages_from_telegram_channel(
    channel_url: str,
    limit: int = 10
) -> list[RSSItemSchema]:
    """
    Fetches messages from a Telegram channel using Telethon.

    :param channel_url: The URL of the Telegram channel.
    :param limit: The maximum number of messages to fetch.

    :return: A list of RSSItemSchema containing the messages.
    """
    channel_name = channel_url.replace("https://t.me/", "").rstrip("/")
    client: TelegramClient = get_tg_client()
    messages: list[RSSItemSchema] = []
    async with client:
        message: Message
        async for message in client.iter_messages(
            entity=channel_name,
            limit=limit
        ):
            if message.text:
                messages.append(
                    RSSItemSchema(
                        title=(
                            message.raw_text[:50] if message.text
                            else "No Title"
                        ),
                        description=message.raw_text or "",
                        link=f"https://t.me/{channel_name}/{message.id}",
                        pub_date=message.date,
                    )
                )
        return messages


async def telegram_producer() -> None:
    channel_urls = await get_sources(telegram=True)
    if not channel_urls:
        logger.info("No Telegram channels configured.")
        return
    channel_urls_list = list(channel_urls.values())
    task_list = []
    news_items: list[RSSItemSchema] = []
    for url in channel_urls_list:
        task_list.append(get_messages_from_telegram_channel(url))
    results = await asyncio.gather(*task_list, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            # TODO: there's obviously not enough data in logging
            logger.error(f"Error fetching messages: {result}")
            continue
        else:
            news_items.extend(result)
    await add_news_to_db(news_items)
