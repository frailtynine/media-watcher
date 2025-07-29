import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ai_news_bot.db.models.users import UserRead


class RSSItemSchema(BaseModel):
    """
    Schema for RSS item.
    """

    title: str
    link: str | None
    description: str | None
    pub_date: datetime


class NewsTaskBaseSchema(BaseModel):
    """
    Base Schema for news tasks.
    """

    title: str
    description: str
    end_date: datetime | None
    link: str | None = None

    model_config = ConfigDict(from_attributes=True)


class NewsTaskCreateSchema(NewsTaskBaseSchema):
    """Schema for creating news tasks."""


class NewsTaskUpdateSchema(NewsTaskBaseSchema):
    """Schema for updating news tasks."""

    is_active: bool | None = None
    end_date: datetime | None = None


class NewsTaskRedisSchema(NewsTaskBaseSchema):
    """Schema for news tasks used in Redis messages."""

    id: int
    is_active: bool
    user_id: uuid.UUID
    end_date: datetime
    created_at: datetime
    positives: list[RSSItemSchema] | None = None
    false_positives: list[RSSItemSchema] | None = None
    result: bool


class NewsTaskReadSchema(NewsTaskBaseSchema):
    """
    Schema for reading news tasks.
    """

    id: int
    is_active: bool
    user: UserRead
    end_date: datetime | None
    created_at: datetime
    positives: list[RSSItemSchema] | None
    false_positives: list[RSSItemSchema] | None
