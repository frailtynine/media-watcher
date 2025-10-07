from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime, Integer

from ai_news_bot.db.base import Base
from sqlalchemy import UniqueConstraint


class TelegramUser(Base):
    """Model for Telegram user."""

    __tablename__ = "tg_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tg_chat_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    __table_args__ = (
        UniqueConstraint(
            'tg_id', 'tg_chat_id',
            name='uq_tg_user_tg_id_tg_chat_id'
        ),
    )
