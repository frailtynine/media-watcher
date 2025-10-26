from ai_news_bot.db.base import Base
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    deepseek: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    deepl: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    rss_urls: Mapped[dict] = mapped_column(
        JSON,
        default={},
    )
    tg_urls: Mapped[dict] = mapped_column(
        JSON,
        default={},
    )
