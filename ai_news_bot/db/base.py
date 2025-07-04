from sqlalchemy.orm import DeclarativeBase

from ai_news_bot.db.meta import meta


class Base(DeclarativeBase):
    """Base for all models."""

    metadata = meta
