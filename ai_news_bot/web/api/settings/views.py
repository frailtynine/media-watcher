from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.settings import settings_crud
from ai_news_bot.db.dependencies import get_db_session
from ai_news_bot.db.models.users import User, current_active_user
from ai_news_bot.web.api.settings.schema import (
    SettingsSchema,
    SourceRequestSchema,
    SourceType,
    ApiSettingsSchema
)
from ai_news_bot.web.api.settings.validators import (
    validate_telegram_channel_url,
    validate_rss_url
)


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
    updated_settings: ApiSettingsSchema,
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


@router.post("/add_source")
async def add_source(
    request: SourceRequestSchema,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> dict[str, str | int]:
    if request.source_type == SourceType.RSS:
        is_valid, result = await validate_rss_url(request.source_url)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"{result}"
            )
        settings = await settings_crud.add_source_to_dict(
            session=session,
            field_name="rss_urls",
            source_name=request.source_name,
            url=result,
        )
        if settings:
            return {
                "detail": result,
                "status": 200,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to add RSS source."
            )
    elif request.source_type == SourceType.TELEGRAM:
        is_valid, result = await validate_telegram_channel_url(
            request.source_url
        )
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"{result}"
            )
        settings = await settings_crud.add_source_to_dict(
            session=session,
            field_name="tg_urls",
            source_name=request.source_name,
            url=result,
        )
        if settings:
            return {
                "detail": result,
                "status": 200,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to add Telegram channel."
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid source type. Must be 'rss' or 'telegram'."
        )


@router.delete("/remove_source")
async def remove_source(
    request: SourceRequestSchema,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> dict[str, str]:
    field_name: str = (
        "rss_urls" if request.source_type == SourceType.RSS
        else "tg_urls"
    )
    if not field_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid source type. Must be 'rss' or 'telegram'."
        )
    settings = await settings_crud.remove_source_from_dict(
        session=session,
        field_name=field_name,
        source_name=request.source_name,
    )
    if settings:
        return {
            "detail": f"{request.source_type} source removed successfully."
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove {request.source_type} source."
        )
