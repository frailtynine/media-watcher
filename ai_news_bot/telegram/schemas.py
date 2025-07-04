from pydantic import BaseModel


class TelegramUser(BaseModel):
    """
    Schema for Telegram user.
    """

    tg_id: int
    tg_chat_id: int
