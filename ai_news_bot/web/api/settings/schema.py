from pydantic import BaseModel, ConfigDict
from enum import Enum


class SettingsSchema(BaseModel):
    deepseek: str | None = None
    deepl: str | None = None
    rss_urls: dict
    tg_urls: dict

    model_config = ConfigDict(
        from_attributes=True
    )


class ApiSettingsSchema(BaseModel):
    deepseek: str | None = None
    deepl: str | None = None


class SourceType(str, Enum):
    TELEGRAM = "telegram"
    RSS = "rss"


class SourceRequestSchema(BaseModel):
    source_url: str
    source_name: str
    source_type: SourceType
