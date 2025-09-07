import uuid
from datetime import datetime

from pydantic import BaseModel


class EventTranslation(BaseModel):
    language_code: str
    title: str
    description: str
    rules: str


class EventCreate(BaseModel):
    id: str
    title: str
    description: str
    created_at: datetime
    results_at: datetime
    ends_at: datetime
    translations: dict[str, EventTranslation]
    rules: str


class EventResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    created_at: datetime
    results_at: datetime
    ends_at: datetime
    translations: dict[str, EventTranslation]
    false_positives: list[dict] = []
    positives: list[dict] = []
    rules: str
    is_active: bool

    class Config:
        from_attributes = True  # For SQLAlchemy model conversion
