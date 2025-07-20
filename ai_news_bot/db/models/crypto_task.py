import uuid
from datetime import datetime, time
from typing import TYPE_CHECKING
from enum import Enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import DateTime, String, Text, Time

from ai_news_bot.db.base import Base

if TYPE_CHECKING:
    from ai_news_bot.db.models.users import User


class CryptoTaskType(str, Enum):
    """Enum for crypto task types."""

    UP = "up"
    DOWN = "down"
    PRICE = "price"


class CryptoTask(Base):
    """Model for crypto task."""

    __tablename__ = "crypto_task"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(length=200), nullable=False)
    description: Mapped[str] = mapped_column(Text(length=5000))
    is_active: Mapped[bool] = mapped_column(default=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    start_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="crypto_tasks")
    start_point: Mapped[float] = mapped_column(nullable=True, default=None)
    end_point: Mapped[float] = mapped_column(nullable=False, default=None)
    measurement_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(String(length=50), nullable=False)
    type: Mapped[CryptoTaskType] = mapped_column(
        String(length=10),
        nullable=False,
        default=CryptoTaskType.PRICE,
    )

    def __repr__(self):
        return (
            f"<CryptoTask(id={self.id}, title={self.title}, "
            f"is_active={self.is_active}, end_date={self.end_date})>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "is_active": self.is_active,
            "end_date": self.end_date,
            "created_at": self.created_at,
            "user_id": self.user_id,
            "start_point": self.start_point,
            "end_point": self.end_point,
            "measurement_time": self.measurement_time,
            "ticker": self.ticker,
            "type": self.type.value,
        }
