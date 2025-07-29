import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import JSON, DateTime, String, Text

from ai_news_bot.db.base import Base

if TYPE_CHECKING:
    from ai_news_bot.db.models.users import User


class NewsTask(Base):
    """Model for news task."""

    __tablename__ = "news_task"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(length=200), nullable=False)
    description: Mapped[str] = mapped_column(Text(length=5000))
    is_active: Mapped[bool] = mapped_column(default=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(back_populates="tasks")
    false_positives: Mapped[list[dict]] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    positives: Mapped[list[dict]] = mapped_column(
        JSON,
        default=list,
        server_default="[]",
    )
    link: Mapped[str] = mapped_column(
        String(length=500),
        nullable=True,
        default=None,
    )

    def __repr__(self):
        return (
            f"<NewsTask(id={self.id}, title={self.title}, "
            f"description={self.description[:20]}, "
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
            "false_positives": self.false_positives,
            "positives": self.positives,
            "link": self.link,
        }
