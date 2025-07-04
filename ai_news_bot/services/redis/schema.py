from pydantic import BaseModel

from ai_news_bot.web.api.news_task.schema import (
    NewsTaskRedisSchema,
    RSSItemSchema,
)


class RedisNewsMessageSchema(BaseModel):
    """
    Schema for messages published to Redis.
    Contains news and task information.
    """

    news: RSSItemSchema
    task: NewsTaskRedisSchema

    model_config = {
        "arbitrary_types_allowed": True,
    }
