import pytest
from datetime import datetime, timedelta

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.telegram.schemas import TelegramUser
from ai_news_bot.db.models.users import User
from ai_news_bot.web.api.news_task.schema import NewsTaskCreateSchema
from ai_news_bot.telegram.utils import clear_html_tags


@pytest.mark.anyio
async def test_telegram_user_crud(
    fastapi_app: FastAPI,
    dbsession: AsyncSession,
    test_user: str,
) -> None:
    """Tests TelegramUserCRUD methods."""
    # Test creating a new Telegram user
    new_user = TelegramUser(
        tg_id=123456789,
        tg_chat_id=987654321,
    )
    created_user = await telegram_user_crud.create(
        session=dbsession, obj_in=new_user
    )
    assert created_user.tg_id == new_user.tg_id

    # Test retrieving all chat IDs

    # Test adding a task to a user
    new_task = NewsTaskCreateSchema(
        title="CRUD Test Task",
        description="This is a test task",
        end_date=(datetime.now() + timedelta(days=7)),
    )
    user = await dbsession.get(User, test_user)
    created_task = await news_task_crud.create(
        session=dbsession,
        obj_in=new_task,
        user=user,
    )
    updated_user = await telegram_user_crud.add_task_to_user(
        session=dbsession,
        tg_id=new_user.tg_id,
        tg_chat_id=new_user.tg_chat_id,
        task=created_task,
    )
    assert created_task in updated_user.tasks

    chat_ids = await telegram_user_crud.get_all_chat_ids(
        session=dbsession,
        task_id=created_task.id
    )
    assert new_user.tg_chat_id in chat_ids

    # Test removing a task from a user
    updated_user = await telegram_user_crud.remove_task_from_user(
        session=dbsession,
        tg_id=new_user.tg_id,
        tg_chat_id=new_user.tg_chat_id,
        task=created_task,
    )
    assert created_task not in updated_user.tasks


@pytest.mark.anyio
def test_clear_html_tags() -> None:
    """Tests clear_html_tags function."""
    html_text = "<p>This is a <b>bold</b> move.</p>"
    expected_text = "This is a bold move."
    assert clear_html_tags(html_text) == expected_text
