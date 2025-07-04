from ai_news_bot.db.crud.base import BaseCRUD
from ai_news_bot.db.models.crypto_task import CryptoTask


class CryptoTaskCRUD(BaseCRUD):
    pass


crypto_task_crud = CryptoTaskCRUD(CryptoTask)
