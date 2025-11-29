from pydantic import BaseModel, ConfigDict


class SettingsSchema(BaseModel):
    deepseek: str | None = None

    model_config = ConfigDict(
        from_attributes=True
    )


class ApiSettingsSchema(BaseModel):
    deepseek: str | None = None
