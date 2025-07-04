import contextlib
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.requests import Request

from ai_news_bot.settings import settings

_standalone_engine = create_async_engine(str(settings.db_url))
_standalone_session_factory = async_sessionmaker(
    _standalone_engine,
    expire_on_commit=False,
)


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Create and get database session.

    :param request: current request.
    :yield: database session.
    """
    session: AsyncSession = request.app.state.db_session_factory()

    try:
        yield session
    finally:
        await session.commit()
        await session.close()


@contextlib.asynccontextmanager
async def get_standalone_session():
    """Get a database session outside of FastAPI context."""
    session = _standalone_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
