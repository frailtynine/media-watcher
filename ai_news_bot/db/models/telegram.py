from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import DateTime, Integer
from sqlalchemy import UniqueConstraint, ForeignKey, Table, Column

from ai_news_bot.db.base import Base
from ai_news_bot.db.models.news_task import NewsTask


tg_user_news_task = Table(
    'tg_user_news_task',
    Base.metadata,
    Column(
        'tg_user_id',
        ForeignKey('tg_user.id'),
        primary_key=True
    ),
    Column(
        'news_task_id',
        ForeignKey('news_task.id'),
        primary_key=True
    ),
)


class TelegramUser(Base):
    """Model for Telegram user."""

    __tablename__ = "tg_user"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    tg_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tg_chat_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    tasks: Mapped[list["NewsTask"]] = relationship(
        secondary=tg_user_news_task,
        back_populates="tg_users",
    )

    __table_args__ = (
        UniqueConstraint(
            'tg_id', 'tg_chat_id',
            name='uq_tg_user_tg_id_tg_chat_id'
        ),
    )
