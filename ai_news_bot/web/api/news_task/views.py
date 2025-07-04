from fastapi import APIRouter, Depends, HTTPException, WebSocket
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.dependencies import get_db_session
from ai_news_bot.db.models.users import User, current_active_user
from ai_news_bot.web.api.news_task.schema import (
    NewsTaskCreateSchema,
    NewsTaskReadSchema,
    NewsTaskUpdateSchema,
)

router = APIRouter()


@router.post("/", response_model=NewsTaskReadSchema)
async def create_news_task(
    new_task: NewsTaskCreateSchema,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> NewsTaskReadSchema:
    """
    Create a new news task.

    :param new_task: The task to be created.
    :param session: The database session.
    :return: The created task.
    """
    return await news_task_crud.create(session=session, obj_in=new_task, user=user)


@router.get("/", response_model=list[NewsTaskReadSchema])
async def get_news_tasks(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> list[NewsTaskReadSchema]:
    """
    Get all news tasks for the current user.

    :return: A list of news tasks.
    """
    return await news_task_crud.get_all_objects(session=session, user=user)


@router.get("/{task_id}", response_model=NewsTaskReadSchema)
async def get_news_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> NewsTaskReadSchema:
    """
    Get a specific news task by ID.

    :param task_id: The ID of the task to retrieve.

    :return: The requested news task.
    """
    return await news_task_crud.get_object_by_id(
        session=session,
        obj_id=task_id,
        user=user,
    )


@router.delete("/{task_id}")
async def delete_news_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> None:
    """
    Delete a specific news task by ID.

    :param task_id: The ID of the task to delete.
    """
    is_deleted = await news_task_crud.delete_object_by_id(
        session=session,
        obj_id=task_id,
        user=user,
    )
    if not is_deleted:
        raise HTTPException(status_code=404, detail="News task not found.")


@router.put("/{task_id}", response_model=NewsTaskReadSchema)
async def update_news_task(
    task_id: int,
    updated_task: NewsTaskUpdateSchema,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user),
) -> NewsTaskReadSchema:
    """
    Update a specific news task by ID.

    :param task_id: The ID of the task to update.
    :param updated_task: The updated task data.
    :return: The updated news task.
    """
    updated_news_task = await news_task_crud.update(
        session=session,
        obj_id=task_id,
        obj_in=updated_task,
        user=user,
    )
    if not updated_news_task:
        raise HTTPException(status_code=404, detail="News task not found.")
    return updated_news_task


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    await websocket.accept()
    redis_pool = websocket.app.state.redis_pool
    async with Redis(connection_pool=redis_pool) as redis:
        pubsub = redis.pubsub()
        await pubsub.subscribe("relevant_news")
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    await websocket.send_text(message["data"].decode())
        except Exception as e:
            raise e
