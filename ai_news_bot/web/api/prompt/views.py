from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.web.api.prompt.schema import PromptRead, PostExample
from ai_news_bot.db.dependencies import get_db_session
from ai_news_bot.db.models.users import User, current_active_user
from ai_news_bot.db.crud.prompt import crud_prompt


router = APIRouter()


@router.get("/", response_model=PromptRead)
async def read_prompt(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
):
    """
    Get the current prompt configuration.

    :param session: Database session.
    :param user: Current active user.
    :return: The current prompt configuration.
    """
    return await crud_prompt.get_or_create(session=session)


@router.put("/", response_model=PromptRead)
async def update_prompt(
    prompt: PromptRead,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
):
    """
    Update the current prompt configuration.

    :param prompt: The updated prompt configuration.
    :param session: Database session.
    :param user: Current active user.
    :return: The updated prompt configuration.
    """
    updated_prompt = await crud_prompt.update(
        session=session,
        obj_id=prompt.id,
        obj_in=prompt
    )
    return updated_prompt


@router.post("/reset", response_model=PromptRead)
async def reset_prompt_to_defaults(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
):
    """
    Reset the prompt configuration to default values.

    :param session: Database session.
    :param user: Current active user.
    :return: The reset prompt configuration.
    """
    return await crud_prompt.reset_to_default(session=session)


@router.post("/examples", response_model=PromptRead)
async def add_post_example(
    example: PostExample,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
):
    """
    Add a new post example to the prompt.

    :param example: The post example to add.
    :param session: Database session.
    :param user: Current active user.
    :return: The updated prompt configuration.
    """
    return await crud_prompt.add_post_example(session, example.example)


@router.post("/examples/delete", response_model=PromptRead)
async def delete_post_example(
    example: PostExample,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
):
    """
    Delete a post example from the prompt.

    :param example: The post example to delete.
    :param session: Database session.
    :param user: Current active user.
    :return: The updated prompt configuration.
    """
    try:
        updated_prompt = await crud_prompt.remove_post_example(
            session,
            example.example
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return updated_prompt
