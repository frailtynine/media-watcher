from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.settings import settings_crud
from ai_news_bot.db.dependencies import get_db_session
from ai_news_bot.db.models.users import User, current_active_user
from ai_news_bot.web.api.settings.schema import SettingsSchema


router = APIRouter()


@router.get("/", response_model=SettingsSchema, name="get_settings")
async def get_settings(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> SettingsSchema:
    """
    Retrieve the application settings.

    :param session: The database session.
    :param user: The current active user.
    :return: The application settings.
    """
    settings = await settings_crud.get_all_objects(session=session)
    if not settings:
        settings_obj = await settings_crud.create(
            session=session,
            obj_in=SettingsSchema(
                deepseek=None,
                deepl=None,
                rss_urls={},
                tg_urls={},
            )
        )
        return settings_obj
    return settings[0]


@router.put("/", response_model=SettingsSchema, name="update_settings")
async def update_settings(
    updated_settings: SettingsSchema,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> SettingsSchema:
    """
    Update the application settings.

    :param updated_settings: The new settings data.
    :param session: The database session.
    :param user: The current active user.
    :return: The updated application settings.
    """
    settings = await settings_crud.get_all_objects(session=session)
    if not settings:
        return await settings_crud.create(
            session=session,
            obj_in=updated_settings
        )
    settings_obj = settings[0]
    return await settings_crud.update(
        session=session,
        obj_id=settings_obj.id,
        obj_in=updated_settings,
    )
