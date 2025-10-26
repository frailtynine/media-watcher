from fastapi.routing import APIRouter

from ai_news_bot.web.api import (
    echo,
    monitoring,
    news_task,
    prompt,
    redis,
    users,
    settings
)

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(users.router)
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])
api_router.include_router(redis.router, prefix="/redis", tags=["redis"])
api_router.include_router(
    news_task.router,
    prefix="/news_task",
    tags=["news_task"],
)
api_router.include_router(prompt.router, prefix="/prompt", tags=["prompt"])
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"],
)
# Note: The order of inclusion matters for path matching.
