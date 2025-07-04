import asyncio
import logging
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.dependencies import get_standalone_session
from ai_news_bot.settings import settings
from ai_news_bot.telegram.schemas import TelegramUser
from ai_news_bot.telegram.utils import parse_rsss_item

logger = logging.getLogger(__name__)

# Global bot instance
bot_app: Optional[Application] = None
task_message_queue: asyncio.Queue = asyncio.Queue()
message_queue: asyncio.Queue = asyncio.Queue()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    tg_user = TelegramUser(
        tg_id=update.message.from_user.id,
        tg_chat_id=update.message.chat.id,
    )
    async with get_standalone_session() as session:
        await telegram_user_crud.create(session=session, obj_in=tg_user)
        await update.message.reply_text(
            "Hello! I'm your AI News Bot. I'll notify you about relevant news.",
        )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /stop command."""
    tg_user = TelegramUser(
        tg_id=update.message.from_user.id,
        tg_chat_id=update.message.chat.id,
    )
    async with get_standalone_session() as session:
        is_deleted = await telegram_user_crud.delete_user(
            session=session,
            tg_id=tg_user.tg_id,
        )
        await update.message.reply_text(
            (
                "You have been unsubscribed from news notifications."
                if is_deleted
                else "Failed to unsubscribe. You may not be subscribed."
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
    async with get_standalone_session() as session:
        if ":" in callback_data:
            # Parse callback data (format: "action:id")
            action, task_id = callback_data.split(":", 1)
            if action == "stop":
                await news_task_crud.stop_task(
                    news_task_id=int(task_id),
                    session=session,
                )
            elif action == "irr":
                news_item = parse_rsss_item(query)
                if news_item is None:
                    await query.message.reply_text("Failed to parse news item.")
                    return
                else:
                    await news_task_crud.add_false_positive(
                        news=news_item,
                        news_task_id=int(task_id),
                        session=session,
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
        bot_app = Application.builder().token(settings.tg_bot_token).build()

        # Add handlers
        bot_app.add_handler(CommandHandler("start", start_command))
        bot_app.add_handler(CommandHandler("stop", stop_command))
        bot_app.add_handler(CallbackQueryHandler(handle_callback_query))
        await bot_app.initialize()
        await bot_app.start()

        asyncio.create_task(bot_app.updater.start_polling())

        # Start message queue processor
        # asyncio.create_task(process_message_queue())
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
            await send_task_message(
                chat_id=message_data["chat_id"],
                text=message_data["text"],
                task_id=message_data["task_id"],
            )
            task_message_queue.task_done()
        except Exception as e:
            logger.error(f"Error processing message from queue: {e}")
        await asyncio.sleep(0.1)


async def process_message_queue() -> None:
    """Background task that processes messages from the queue."""
    while True:
        try:
            message_data = await message_queue.get()
            await send_message(
                chat_id=message_data["chat_id"],
                text=message_data["text"],
            )
            message_queue.task_done()
        except Exception as e:
            logger.error(f"Error processing message from queue: {e}")
        await asyncio.sleep(0.1)


async def queue_message(chat_id: int, text: str) -> None:
    """
    Add a message to the queue for sending.

    Args:
        chat_id: Telegram chat ID to send the message to
        text: Message text
    """
    await message_queue.put(
        {
            "chat_id": chat_id,
            "text": text,
        },
    )


async def queue_task_message(chat_id: int, text: str, task_id: str) -> None:
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
        },
    )


async def send_task_message(
    chat_id: int,
    text: str,
    task_id: str,
) -> int:
    """
    Send a message with "stop" and "irrelevant" buttons.

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

    keyboard = [
        [
            InlineKeyboardButton("Stop", callback_data=f"stop:{task_id}"),
            InlineKeyboardButton("Irrelevant", callback_data=f"irr:{task_id}"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await asyncio.wait_for(
        bot_app.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
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
            text=text,
        ),
        timeout=5.00,
    )
