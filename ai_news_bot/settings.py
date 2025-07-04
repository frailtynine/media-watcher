import enum
import os
from pathlib import Path
from tempfile import gettempdir
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL

TEMP_DIR = Path(gettempdir())


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False

    # Current environment
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO
    users_secret: str = os.getenv("USERS_SECRET", "")
    # Variables for the database
    db_file: Path = TEMP_DIR / "db.sqlite3"
    db_echo: bool = False
    # Variables for Redis
    redis_host: str = "ai_news_bot-redis"
    redis_port: int = 6379
    redis_user: Optional[str] = None
    redis_pass: Optional[str] = None
    redis_base: Optional[int] = None
    # For testing purposes.
    # TODO: in prod create a model for tokens
    deepseek: Optional[str] = None
    tg_bot_test_token: Optional[str] = None
    tg_bot_token: Optional[str] = None
    coinmarketcap_api_key: Optional[str] = None

    @property
    def db_url(self) -> URL:
        """
        Assemble database URL from settings.

        :return: database URL.
        """
        return "sqlite+aiosqlite:///./fastapi.db"

    @property
    def redis_url(self) -> URL:
        """
        Assemble REDIS URL from settings.

        :return: redis URL.
        """
        path = ""
        if self.redis_base is not None:
            path = f"/{self.redis_base}"
        return URL.build(
            scheme="redis",
            host=self.redis_host,
            port=self.redis_port,
            user=self.redis_user,
            password=self.redis_pass,
            path=path,
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AI_NEWS_BOT_",
        env_file_encoding="utf-8",
    )


settings = Settings()
