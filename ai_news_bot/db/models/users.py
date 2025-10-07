# type: ignore
import uuid
import contextlib

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, schemas
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase
)
from fastapi_users.exceptions import UserAlreadyExists

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, relationship

from ai_news_bot.db.base import Base
from ai_news_bot.db.dependencies import get_db_session, get_standalone_session
from ai_news_bot.db.models.news_task import NewsTask
from ai_news_bot.settings import settings


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Represents a user entity."""

    tasks: Mapped[list[NewsTask]] = relationship(back_populates="user")


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Represents a read command for a user."""


class UserCreate(schemas.BaseUserCreate):
    """Represents a create command for a user."""


class UserUpdate(schemas.BaseUserUpdate):
    """Represents an update command for a user."""


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """Manages a user session and its tokens."""

    reset_password_token_secret = settings.users_secret
    verification_token_secret = settings.users_secret


async def get_user_db(
    session: AsyncSession = Depends(get_db_session),
) -> SQLAlchemyUserDatabase:
    """
    Yield a SQLAlchemyUserDatabase instance.

    :param session: asynchronous SQLAlchemy session.
    :yields: instance of SQLAlchemyUserDatabase.
    """
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> UserManager:
    """
    Yield a UserManager instance.

    :param user_db: SQLAlchemy user db instance
    :yields: an instance of UserManager.
    """
    yield UserManager(user_db)


def get_jwt_strategy() -> JWTStrategy:
    """
    Return a JWTStrategy in order to instantiate it dynamically.

    :returns: instance of JWTStrategy with provided settings.
    """
    return JWTStrategy(secret=settings.users_secret, lifetime_seconds=None)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
auth_jwt = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

backends = [
    auth_jwt,
]

api_users = FastAPIUsers[User, uuid.UUID](get_user_manager, backends)

current_active_user = api_users.current_user(active=True)


async def create_user(email: str, password: str, is_superuser: bool = False):
    """ Create a user if it does not exist. """
    try:
        async with get_standalone_session() as session:
            user_db = SQLAlchemyUserDatabase(session, User)
            user_manager = UserManager(user_db)
            user = await user_manager.create(
                UserCreate(
                    email=email,
                    password=password,
                    is_superuser=is_superuser
                )
            )
            print(f"User created {user}")
    except UserAlreadyExists:
        print(f"User {email} already exists")
