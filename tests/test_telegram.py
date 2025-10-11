import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.telegram.schemas import TelegramUser
from ai_news_bot.telegram.utils import clear_html_tags


@pytest.mark.anyio
async def test_telegram_user_crud(
    fastapi_app: FastAPI,
    dbsession: AsyncSession,
) -> None:
    """Tests TelegramUserCRUD methods."""
    # Test creating a new Telegram user
    new_user = TelegramUser(
        tg_id=123456789,
        tg_chat_id=987654321,
    )
    created_user = await telegram_user_crud.create(session=dbsession, obj_in=new_user)
    assert created_user.tg_id == new_user.tg_id

    # Test retrieving all chat IDs
    chat_ids = await telegram_user_crud.get_all_chat_ids(session=dbsession)
    assert new_user.tg_chat_id in chat_ids


@pytest.mark.anyio
def test_clear_html_tags() -> None:
    """Tests clear_html_tags function."""
    html_text = "<p>This is a <b>bold</b> move.</p>"
    expected_text = "This is a bold move."
    assert clear_html_tags(html_text) == expected_text

