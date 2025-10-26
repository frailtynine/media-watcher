from pydantic import BaseModel, ConfigDict


class SettingsSchema(BaseModel):
    deepseek: str | None = None
    deepl: str | None = None
    rss_urls: dict
    tg_urls: dict

    model_config = ConfigDict(
        from_attributes=True
    )
