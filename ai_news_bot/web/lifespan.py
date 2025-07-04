import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ai_news_bot.ai.news_analyzer import news_analyzer
from ai_news_bot.db.meta import meta
from ai_news_bot.services.redis.lifespan import init_redis, shutdown_redis
from ai_news_bot.settings import settings
from ai_news_bot.telegram.bot import setup_bot, shutdown_bot


async def _setup_db(app: FastAPI) -> None:  # pragma: no cover
    """
    Creates connection to the database.

    This function creates SQLAlchemy engine instance,
    session_factory for creating sessions
    and stores them in the application's state property.

    :param app: fastAPI application.
    """
    engine = create_async_engine(str(settings.db_url), echo=settings.db_echo)
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)


@asynccontextmanager
async def lifespan_setup(
    app: FastAPI,
) -> AsyncGenerator[None, None]:  # pragma: no cover
    """
    Actions to run on application startup.

    This function uses fastAPI app to store data
    in the state, such as db_engine.

    :param app: the fastAPI application.
    :return: function that actually performs actions.
    """

    app.middleware_stack = None
    await _setup_db(app)
    init_redis(app)
    await setup_bot()
    news_analyzer_task = asyncio.create_task(news_analyzer(app))
    app.state.news_analyzer_task = news_analyzer_task

    app.middleware_stack = app.build_middleware_stack()

    yield

    if hasattr(app.state, "news_analyzer_task"):
        app.state.news_analyzer_task.cancel()
        try:
            await app.state.news_analyzer_task
        except asyncio.CancelledError:
            pass
    await app.state.db_engine.dispose()

    await shutdown_redis(app)
    await shutdown_bot()
