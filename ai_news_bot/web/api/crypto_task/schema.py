from datetime import datetime, time
from pydantic import BaseModel, Field
import uuid

from ai_news_bot.db.models.crypto_task import CryptoTaskType


class CryptoTaskCreateSchema(BaseModel):
    """Schema for creating a crypto task."""

    title: str = Field(..., max_length=200, description="Title")
    description: str | None = Field(
        None, max_length=5000, description="Description"
    )
    end_date: datetime = Field(..., description="End date")
    start_date: datetime | None = Field(
        None, description="Start date"
    )
    start_point: float | None = Field(None, description="Start point value")
    end_point: float = Field(..., description="End point value")
    measurement_time: time = Field(..., description="Measurement time")
    ticker: str = Field(..., max_length=50, description="Ticker symbol")
    type: CryptoTaskType = Field(
        CryptoTaskType.PRICE, max_length=10, description="Type of task"
    )


class CryptoTaskReadSchema(CryptoTaskCreateSchema):
    """Schema for crypto task."""

    id: int
    is_active: bool
    created_at: datetime
    user_id: uuid.UUID
