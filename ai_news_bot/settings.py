import enum
import os
from pathlib import Path
from tempfile import gettempdir
from typing import Optional
import logging
import logging.config


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


def setup_logging(log_level: LogLevel = LogLevel.INFO) -> None:
    """
    Setup logging configuration.

    :param log_level: The log level to use.
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - "
                    "%(module)s:%(lineno)d - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level.value,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level.value,
                "formatter": "detailed",
                "filename": "ai_news_bot.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "ai_news_bot": {
                "level": log_level.value,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            }
        },
        "root": {
            "level": log_level.value,
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str = "ai_news_bot") -> logging.Logger:
    """
    Get a logger instance.

    :param name: The name of the logger.
    :return: Logger instance.
    """
    return logging.getLogger(name)


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8050
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False
    # cors origins
    cors_origins: list[str] = [""]

    # Current environment
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO
    users_secret: str = os.getenv("USERS_SECRET", "")
    # Variables for the database
    db_file: Path = Path("/app/data/media_watcher_verstka.db")
    db_echo: bool = False
    # Variables for Redis
    redis_host: str = "media-watcher-redis"
    redis_port: int = 6379
    redis_user: Optional[str] = None
    redis_pass: Optional[str] = None
    redis_base: Optional[int] = None
    # For testing purposes.
    # TODO: in prod create a model for tokens
    deepseek: Optional[str] = None
    deepl: Optional[str] = None
    tg_bot_test_token: Optional[str] = None
    tg_bot_token: Optional[str] = None
    admin_email: Optional[str] = None
    admin_password: Optional[str] = None

    @property
    def db_url(self) -> URL:
        """
        Assemble database URL from settings.

        :return: database URL.
        """
        return f"sqlite+aiosqlite:///{self.db_file}"

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
        env_prefix="MEDIA_WATCHER_",
        env_file_encoding="utf-8",
    )

    def setup_logging(self) -> None:
        """Setup logging with the current log level."""
        setup_logging(self.log_level)


settings = Settings()
settings.setup_logging()
