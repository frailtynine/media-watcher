# import pytest

# from datetime import datetime
# from unittest.mock import MagicMock

# from ai_news_bot.ai.news_analyzer import process_news, role
# from ai_news_bot.web.api.news_task.schema import RSSItemSchema
# from ai_news_bot.db.models.news_task import NewsTask


# @pytest.mark.anyio
# async def test_process_news_real_api():
#     """Test process_news with real Deepseek API."""
#     # Create sample news and task
#     news = RSSItemSchema(
#         title="Russia and Ukraine negotiations break down",
#         link="https://example.com/news",
#         description=(
#             "Recent peace talks between Russia and Ukraine have broken "
#             "without agreement."
#         ),
#         pub_date=datetime.now()
#     )

#     # Create a mock task
#     task = MagicMock(spec=NewsTask)
#     task.title = "Ukraine Peace Negotiations"
#     task.description = (
#         "Will resolve to 'Yes' if peace talks "
#         "between Russia and Ukraine break down."
#     )
#     task.false_positives = []

#     # Test with real API
#     result = process_news(
#         news=news,
#         news_task=task,
#         initial_prompt=role
#     )
#     assert isinstance(result, bool)
