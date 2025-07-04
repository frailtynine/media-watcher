# import asyncio
# import pytest
# from unittest.mock import patch, AsyncMock, MagicMock

# from ai_news_bot.telegram.bot import (
#     setup_bot,
#     shutdown_bot,
#     queue_task_message,
#     message_queue,
# )


# @pytest.fixture
# def mock_settings():
#     """Mock settings with a test Telegram token."""
#     with patch('ai_news_bot.telegram.bot.settings') as mock_settings:
#         mock_settings.tg_bot_token = "test_token"
#         yield mock_settings


# @pytest.fixture
# def mock_telegram_app():
#     """Mock for the telegram Application class."""
#     with patch(
#         'ai_news_bot.telegram.bot.Application', autospec=True
#     ) as mock_app_class:
#         # Create mock for the Application instance
#         mock_app_instance = AsyncMock()

#         # Configure builder chain to return our mock instance
#         mock_builder = MagicMock()
#         mock_builder.token.return_value.build.return_value = mock_app_instance
#         mock_app_class.builder.return_value = mock_builder

#         # Setup required mocks for methods used in setup_bot
#         mock_app_instance.initialize = AsyncMock()
#         mock_app_instance.start = AsyncMock()
#         mock_app_instance.stop = AsyncMock()
#         mock_app_instance.shutdown = AsyncMock()
#         mock_app_instance.updater.start_polling = AsyncMock()

#         # Add handler mock
#         mock_app_instance.add_handler = MagicMock()

#         yield mock_app_instance


# @pytest.fixture
# def mock_create_task():
#     """Mock asyncio.create_task to prevent background tasks from starting."""
#     with patch('ai_news_bot.telegram.bot.asyncio.create_task') as mock:
#         yield mock


# @pytest.mark.anyio
# async def test_telegram_bot_setup_teardown(
#     mock_settings,
#     mock_telegram_app,
#     mock_create_task
# ):
#     """
#     A simple test that initializes and then cleans up the Telegram bot.

#     This test verifies that:
#     1. The bot can be initialized without errors
#     2. Required methods are called during initialization
#     3. The bot can be shut down properly
#     """
#     # Set up the bot
#     app = await setup_bot()

#     # Verify app instance
#     assert app is mock_telegram_app

#     # Verify initialization methods were called
#     mock_telegram_app.initialize.assert_called_once()
#     mock_telegram_app.start.assert_called_once()
#     mock_telegram_app.updater.start_polling.assert_called_once()

#     # Verify handlers were added (at least 2 handlers should be added)
#     assert mock_telegram_app.add_handler.call_count >= 2

#     # Verify background tasks were created (at least 4 tasks)
#     assert mock_create_task.call_count >= 4

#     # Shut down the bot
#     await shutdown_bot()

#     # Verify shutdown methods were called
#     mock_telegram_app.stop.assert_called_once()
#     mock_telegram_app.shutdown.assert_called_once()


# @pytest.fixture
# async def clear_message_queue():
#     """Clear the message queue before and after the test."""
#     # Clear the queue before the test
#     while not message_queue.empty():
#         try:
#             message_queue.get_nowait()
#             message_queue.task_done()
#         except asyncio.QueueEmpty:
#             break

#     yield

#     # Clear the queue after the test
#     while not message_queue.empty():
#         try:
#             message_queue.get_nowait()
#             message_queue.task_done()
#         except asyncio.QueueEmpty:
#             break


# @pytest.mark.anyio
# async def test_message_queue(clear_message_queue):
#     """
#     A simple test for the telegram message queue.

#     This test verifies that:
#     1. Messages can be added to the queue
#     2. The queue follows FIFO order
#     """
#     # Test data
#     chat_id = 123456
#     text1 = "Test message 1"
#     text2 = "Test message 2"
#     task_id = "test-task-id"

#     # Verify the queue is empty at the start
#     assert message_queue.empty()

#     # Add a message to the queue
#     await queue_task_message(chat_id, text1, task_id)

#     # Verify the queue is not empty
#     assert not message_queue.empty()

#     # Add another message
#     await queue_task_message(chat_id, text2, task_id)

#     # Verify the queue size (should be 2)
#     assert message_queue.qsize() == 2

#     # Get the first message and verify it's the first one we added
#     message1 = await message_queue.get()
#     assert message1["text"] == text1

#     # Get the second message and verify it's the second one we added
#     message2 = await message_queue.get()
#     assert message2["text"] == text2

#     # Verify the queue is now empty
#     assert message_queue.empty()
