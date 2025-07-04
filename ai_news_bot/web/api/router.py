from fastapi.routing import APIRouter

from ai_news_bot.web.api import echo, monitoring, news_task, redis, users

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(users.router)
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])
api_router.include_router(redis.router, prefix="/redis", tags=["redis"])
api_router.include_router(news_task.router, prefix="/news_task", tags=["news_task"])
