from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime, Integer

from ai_news_bot.db.base import Base


class TelegramUser(Base):
    """Model for Telegram user."""

    __tablename__ = "tg_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    tg_chat_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
