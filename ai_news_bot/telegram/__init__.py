"""Telegram bot integration for AI News Bot."""

from ai_news_bot.telegram.bot import (
    queue_task_message,
    setup_bot,
    shutdown_bot,
)

__all__ = ["setup_bot", "shutdown_bot", "queue_task_message"]
