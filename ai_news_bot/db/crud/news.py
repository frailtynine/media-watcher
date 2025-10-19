from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.news import News


class CRUDNews(BaseCRUD):
    pass


crud_news = CRUDNews(News)
