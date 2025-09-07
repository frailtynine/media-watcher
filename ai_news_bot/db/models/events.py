import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from ai_news_bot.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, unique=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(5000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
    )
    results_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
    )
    translations: Mapped[dict[str, dict[str, str]]] = mapped_column(
        JSON, nullable=False, default={},
    )
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
    rules: Mapped[str] = mapped_column(
        String(5000), nullable=True, default=None,
    )
    is_active: Mapped[bool] = mapped_column(
        default=False, nullable=False,
    )

    @property
    def link(self) -> str:
        """Generate a link for the event."""
        return (
            f"https://t.me/ft_rm_bot/futurum?"
            f"startapp=event_{self.id}=source_futurumTg"
        )

    def __repr__(self):
        return f"<Event(title={self.title}, description={self.description})>"
