from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.db.dependencies import get_db_session
from ai_news_bot.db.models.users import User, current_active_user
from ai_news_bot.db.crud.crypto_task import crypto_task_crud
from ai_news_bot.web.api.crypto_task.schema import (
    CryptoTaskCreateSchema,
    CryptoTaskReadSchema
)

router = APIRouter()


@router.post("/", response_model=CryptoTaskReadSchema)
async def create_crypto_task(
    task: CryptoTaskCreateSchema,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user)
):
    db_task = await crypto_task_crud.create(session, task, user)
    if not db_task:
        raise HTTPException(status_code=400, detail="Task creation failed")
    return db_task


@router.get("/{task_id}", response_model=CryptoTaskReadSchema)
async def get_crypto_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user)
):
    db_task = await crypto_task_crud.get_object_by_id(session, task_id, user)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.get("/", response_model=list[CryptoTaskReadSchema])
async def get_crypto_tasks(
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user)
):
    db_tasks = await crypto_task_crud.get_all_objects(
        session=session,
        user=user
    )
    return db_tasks


@router.delete("/{task_id}")
async def delete_crypto_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user)
):
    db_task = await crypto_task_crud.get_object_by_id(session, task_id, user)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    await crypto_task_crud.delete_object_by_id(session, db_task.id)
    return {"detail": "Task deleted successfully"}


@router.put("/{task_id}", response_model=CryptoTaskReadSchema)
async def update_crypto_task(
    task_id: int,
    task: CryptoTaskCreateSchema,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_active_user)
):
    db_task = await crypto_task_crud.get_object_by_id(session, task_id, user)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    updated_task = await crypto_task_crud.update(session, db_task.id, task)
    if not updated_task:
        raise HTTPException(status_code=400, detail="Task update failed")
    return updated_task
