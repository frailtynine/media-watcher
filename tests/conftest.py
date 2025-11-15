from typing import Any, AsyncGenerator

import pytest
from fakeredis import FakeServer
from fakeredis.aioredis import FakeConnection
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from redis.asyncio import ConnectionPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ai_news_bot.db.dependencies import get_db_session
from ai_news_bot.db.utils import create_database
from ai_news_bot.services.redis.dependency import get_redis_pool
from ai_news_bot.settings import settings
from ai_news_bot.web.application import get_app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Backend for anyio pytest plugin.

    :return: backend name.
    """
    return "asyncio"


@pytest.fixture(scope="session")
async def _engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create engine and databases.

    :yield: new engine.
    """
    from ai_news_bot.db.meta import meta
    from ai_news_bot.db.models import load_all_models
    import tempfile
    import os
    from pathlib import Path

    load_all_models()

    # Create a temporary database file for testing
    test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")
    os.close(test_db_fd)  # Close the file descriptor

    # Set environment variable to override the database file for tests
    os.environ["MEDIA_WATCHER_DB_FILE"] = test_db_path

    # Reload settings to pick up the new database path
    from ai_news_bot.settings import settings
    settings.db_file = Path(test_db_path)

    await create_database()

    engine = create_async_engine(str(settings.db_url))
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()
        # Clean up the temporary test database file
        import os
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)


@pytest.fixture
async def dbsession(
    _engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get session to database.

    Fixture that returns a SQLAlchemy session with a SAVEPOINT,
    and the rollback to it after the test completes.

    :param _engine: current engine.
    :yields: async session.
    """
    connection = await _engine.connect()
    trans = await connection.begin()

    session_maker = async_sessionmaker(
        connection,
        expire_on_commit=False,
    )
    session = session_maker()

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest.fixture
async def fake_redis_pool() -> AsyncGenerator[ConnectionPool, None]:
    """
    Get instance of a fake redis.

    :yield: FakeRedis instance.
    """
    server = FakeServer()
    server.connected = True
    pool = ConnectionPool(connection_class=FakeConnection, server=server)

    yield pool

    await pool.disconnect()


@pytest.fixture
def fastapi_app(
    dbsession: AsyncSession,
    fake_redis_pool: ConnectionPool,
) -> FastAPI:
    """
    Fixture for creating FastAPI app.

    :return: fastapi app with mocked dependencies.
    """
    application = get_app()
    application.dependency_overrides[get_db_session] = lambda: dbsession
    application.dependency_overrides[get_redis_pool] = lambda: fake_redis_pool
    return application


@pytest.fixture
async def client(
    fastapi_app: FastAPI,
    anyio_backend: Any,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that creates client for requesting server.

    :param fastapi_app: the application.
    :yield: client for the app.
    """
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
        timeout=2.0
    ) as ac:
        yield ac


@pytest.fixture
async def auth_headers(dbsession: AsyncSession, client: AsyncClient) -> dict:
    """Get authentication headers by actually logging in through the API."""

    # Create user with session commit
    from ai_news_bot.db.models.users import UserCreate, User, UserManager
    from fastapi_users.db import SQLAlchemyUserDatabase
    from fastapi_users.exceptions import UserAlreadyExists

    try:
        user_db = SQLAlchemyUserDatabase(dbsession, User)
        user_manager = UserManager(user_db)
        await user_manager.create(
            UserCreate(
                email=settings.admin_email,
                password=settings.admin_password,
                is_superuser=True
            )
        )
        await dbsession.commit()  # Ensure user is committed
    except UserAlreadyExists:
        pass  # User already exists, continue
    except Exception as e:
        raise Exception(f"Error creating user: {e}")

    login_data = {
        "username": settings.admin_email,
        "password": settings.admin_password,
    }
    response = await client.post("/api/auth/jwt/login", data=login_data)

    if response.status_code != 200:
        raise Exception(
            f"Login failed with status {response.status_code}: {response.text}"
        )

    token = response.json().get("access_token")
    if not token:
        raise Exception(f"No access token in response: {response.json()}")

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_user(
    dbsession: AsyncSession,
    client: AsyncClient,
    auth_headers: dict,
) -> str:
    """Create test user and return it."""
    response = await client.get("/api/users/me", headers=auth_headers)
    user = response.json()
    return user.get("id")
