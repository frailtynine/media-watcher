import asyncio
import logging
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes
)
from langdetect import detect

from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.crud.settings import settings_crud
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.settings import settings
from ai_news_bot.telegram.schemas import TelegramUser
from ai_news_bot.web.api.news_task.schema import RSSItemSchema
from ai_news_bot.ai.utils import (
    get_full_text,
    translate_with_ai
)
from ai_news_bot.telegram.utils import chunk_message, clear_html_tags

logger = logging.getLogger(__name__)

# Global bot instance
bot_app: Optional[Application] = None
task_message_queue: asyncio.Queue = asyncio.Queue()


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /start command."""
    tg_user = TelegramUser(
        tg_id=update.message.from_user.id,
        tg_chat_id=update.message.chat.id,
    )
    async with get_standalone_session() as session:
        user = await telegram_user_crud.create(session=session, obj_in=tg_user)
        logger.info(f"User subscribed: {user.tg_id} {user.tg_chat_id}")
        await update.message.reply_text(
            text=(
                "Привет! Я мониторю новости и отправляю их в этот чат. \n\n"
                "Вы теперь на меня подписаны."
            ),
        )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /stop command."""
    tg_user = TelegramUser(
        tg_id=update.message.from_user.id,
        tg_chat_id=update.message.chat.id,
    )
    async with get_standalone_session() as session:
        is_deleted = await telegram_user_crud.delete_session(
            session=session,
            tg_id=tg_user.tg_id,
            tg_chat_id=tg_user.tg_chat_id,
        )
        await update.message.reply_text(
            (
                "Вы от меня отписались."
                if is_deleted
                else "Не удалось отписаться. Возможно, вы не подписаны."
            ),
        )


async def handle_callback_query(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle button clicks."""
    query = update.callback_query
    callback_data = query.data
    await query.answer()
    logger.info(f"Received callback data: {callback_data}")
    async with get_standalone_session() as session:
        if callback_data["action"] == "irr":
            news = RSSItemSchema.model_validate(callback_data["news"])
            await news_task_crud.add_false_positive(
                news=news,
                news_task_id=callback_data["task_id"],
                session=session,
            )
        elif callback_data["action"] == "translate":
            settings = await settings_crud.get_all_objects(session=session)
            if settings:
                deepl_api_key = settings[0].deepl
            if not deepl_api_key:
                logger.warning("Deepl API key not found in settings.")
                await send_message(
                    chat_id=query.message.chat.id,
                    text="Ключ Deepl API не настроен.",
                )
                return
            if "news" in callback_data:
                article = get_full_text(callback_data["news"].link)
                if article:
                    translated_text = await translate_with_ai(article)
                    if len(translated_text) > 4000:
                        chunks = chunk_message(translated_text)
                        for chunk in chunks:
                            await send_message(
                                chat_id=query.message.chat.id,
                                text=chunk,
                            )
                    else:
                        await send_message(
                            chat_id=query.message.chat.id,
                            text=translated_text,
                        )
                else:
                    logger.error((
                        f"Failed to fetch article from "
                        f"{callback_data['news'].link}"
                    ))
                    await send_message(
                        chat_id=query.message.chat.id,
                        text=("Не удалось получить полный текст статьи."),
                    )
            else:
                await send_message(
                    chat_id=query.message.chat.id,
                    text="Что-то пошло не так.",
                )
        else:
            logger.warning(f"Invalid callback data format: {callback_data}")


async def setup_bot() -> Application:
    """Initialize and set up the Telegram bot."""
    global bot_app

    if bot_app is not None:
        logger.info("Bot already initialized")
        return bot_app

    # Create application
    try:
        bot_app = (
            Application.builder()
            .token(
                settings.tg_bot_token,
            )
            .arbitrary_callback_data(
                True,
            )
            .build()
        )
        # Add handlers
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(CommandHandler("stop", stop_command))
        bot_app.add_handler(CallbackQueryHandler(handle_callback_query))
        await bot_app.initialize()
        await bot_app.start()

        asyncio.create_task(bot_app.updater.start_polling())

        # Start message queue processor
        asyncio.create_task(process_task_message_queue())

        logger.info("Telegram bot started successfully")
        return bot_app
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")
        raise


async def shutdown_bot() -> None:
    """Gracefully shut down the Telegram bot."""
    global bot_app
    if bot_app is not None:
        await bot_app.stop()
        await bot_app.shutdown()
        bot_app = None
        logger.info("Telegram bot shutdown complete")


async def process_task_message_queue() -> None:
    """Background task that processes messages from the queue."""
    while True:
        try:
            message_data = await task_message_queue.get()
            if message_data["task_id"]:
                await send_task_message(
                    chat_id=message_data["chat_id"],
                    text=message_data["text"],
                    task_id=message_data["task_id"],
                    news=message_data["news"],
                )
            else:
                await send_message(
                    chat_id=message_data["chat_id"],
                    text=message_data["text"],
                )
            task_message_queue.task_done()
        except Exception as e:
            logger.error(f"Error processing message from queue: {e}")
        await asyncio.sleep(0.1)


async def queue_task_message(
    chat_id: int,
    text: str,
    task_id: str | None = None,
    news: RSSItemSchema | None = None,
) -> None:
    """
    Add a message to the queue for sending.

    Args:
        chat_id: Telegram chat ID to send the message to
        text: Message text
        task_id: ID to include in button callbacks
    """
    await task_message_queue.put(
        {
            "chat_id": chat_id,
            "text": text,
            "task_id": task_id,
            "news": news,
        },
    )


async def send_task_message(
    chat_id: int,
    text: str,
    task_id: str,
    news: RSSItemSchema,
) -> int:
    """
    Send a message with  buttons.

    Args:
        chat_id: Telegram chat ID
        text: Message text
        task_id: ID to include in button callbacks

    Returns:
        Message ID of the sent message
    """
    global bot_app
    if bot_app is None:
        raise RuntimeError("Bot not initialized")
    irr_callback = {
        "action": "irr",
        "task_id": task_id,
        "news": news,
    }
    translate_callback = {
        "action": "translate",
        "task_id": task_id,
        "news": news,
    }
    post_language = detect(news.title)
    keyboard = [
        [
            InlineKeyboardButton(
                "❌",
                callback_data=irr_callback,
            ),
        ],
    ]
    if post_language == "en":
        keyboard[0].append(
            InlineKeyboardButton(
                "🇬🇧 -> 🇷🇺",
                callback_data=translate_callback
            )
        )
        text = await translate_with_ai(news)
    cleared_text = clear_html_tags(text)
    reply_markup = InlineKeyboardMarkup(keyboard)
    disable_web_page_preview = True
    if "https://t.me" in news.link:
        cleared_text = news.link
        disable_web_page_preview = False
    await asyncio.wait_for(
        bot_app.bot.send_message(
            chat_id=chat_id,
            text=cleared_text,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
            parse_mode="Markdown",
            disable_notification=True,
        ),
        timeout=5.00,
    )


async def send_message(chat_id: int, text: str):
    """
    Send a simple message without buttons.

    Args:
        chat_id: Telegram chat ID
        text: Message text

    Returns:
        Message ID of the sent message
    """
    global bot_app
    if bot_app is None:
        raise RuntimeError("Bot not initialized")

    await asyncio.wait_for(
        bot_app.bot.send_message(
            chat_id=chat_id,
            text=clear_html_tags(text),
            parse_mode="Markdown",
        ),
        timeout=5.00,
    )
