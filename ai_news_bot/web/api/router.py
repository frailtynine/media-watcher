from fastapi.routing import APIRouter

from ai_news_bot.web.api import (
    crypto_task,
    echo,
    events,
    monitoring,
    news_task,
    prompt,
    redis,
    users,
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
api_router.include_router(
    crypto_task.router,
    prefix="/crypto_task",
    tags=["crypto_task"],
)
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(prompt.router, prefix="/prompt", tags=["prompt"])
# Note: The order of inclusion matters for path matching.
