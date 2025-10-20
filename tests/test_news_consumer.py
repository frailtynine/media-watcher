from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai_news_bot.ai.news_consumer import (
    add_positive_news,
    news_consumer,
    process_news,
    send_news_to_telegram,
)
from ai_news_bot.db.crud.news import crud_news
from ai_news_bot.db.crud.news_task import news_task_crud
from ai_news_bot.db.crud.prompt import crud_prompt
from ai_news_bot.db.crud.telegram import telegram_user_crud
from ai_news_bot.db.models.news import News
from ai_news_bot.db.models.news_task import NewsTask
from ai_news_bot.db.models.prompt import Prompt
from ai_news_bot.web.api.news_task.schema import RSSItemSchema


# Test fixtures
@pytest.fixture
def sample_news():
    """Create a sample news item for testing."""
    return News(
        id=1,
        title="Test News Title",
        link="https://example.com/news/1",
        description="This is a test news description",
        pub_date=datetime.now(timezone.utc),
        processed=False,
    )


@pytest.fixture
def sample_news_task():
    """Create a sample news task for testing."""
    return NewsTask(
        id=1,
        title="Test Task",
        description="Filter for tech news",
        end_date=datetime.now(timezone.utc),
        is_active=True,
        false_positives=[
            {"title": "Irrelevant News 1", "description": "Not relevant"},
            {"title": "Irrelevant News 2", "description": "Also not relevant"},
        ],
        positives=[],
    )


@pytest.fixture
def sample_prompt():
    """Create a sample prompt for testing."""
    return Prompt(
        id=1,
        role="You are a news filter. Respond with YES or NO only.",
    )


@pytest.mark.anyio
async def test_send_news_to_telegram(sample_news, dbsession: AsyncSession):
    """Test sending news to telegram."""
    chat_ids = [123456789, 987654321]

    with patch.object(
        telegram_user_crud, 'get_all_chat_ids', return_value=chat_ids
    ):
        with patch(
            'ai_news_bot.ai.news_consumer.queue_task_message'
        ) as mock_queue:
            await send_news_to_telegram(sample_news, task_id=1)

            # Verify queue_task_message was called for each chat_id
            assert mock_queue.call_count == 2

            # Check the first call
            call_args = mock_queue.call_args_list[0][1]
            assert call_args['chat_id'] == 123456789
            assert "Test News Title" in call_args['text']
            assert "https://example.com/news/1" in call_args['text']
            assert call_args['task_id'] == "1"
            assert call_args['news'] == sample_news


@pytest.mark.anyio
async def test_process_news_relevant(
    sample_news, sample_news_task, sample_prompt
):
    """Test processing news that is relevant."""
    # Mock the OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "true"

    with patch('ai_news_bot.ai.news_consumer.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value.__aenter__.return_value = mock_client

        result = await process_news(
            news=sample_news,
            news_task=sample_news_task,
            initial_prompt=sample_prompt.role,
        )

        assert result is True

        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.anyio
async def test_process_news_not_relevant(
    sample_news, sample_news_task, sample_prompt
):
    """Test processing news that is not relevant."""
    # Mock the OpenAI response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "false"

    with patch('ai_news_bot.ai.news_consumer.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value.__aenter__.return_value = mock_client

        result = await process_news(
            news=sample_news,
            news_task=sample_news_task,
            initial_prompt=sample_prompt.role,
        )

        assert result is False


@pytest.mark.anyio
async def test_add_positive_news(
    sample_news, sample_news_task, dbsession: AsyncSession
):
    """Test adding positive news to a task."""
    with patch.object(crud_news, 'get_object_by_id', return_value=sample_news):
        with patch.object(
            news_task_crud, 'get_object_by_id', return_value=sample_news_task
        ):
            with patch.object(
                news_task_crud, 'add_positive'
            ) as mock_add_positive:
                await add_positive_news(
                    news_id=sample_news.id,
                    news_task_id=sample_news_task.id,
                )
         
                # Verify add_positive was called
                mock_add_positive.assert_called_once()
                call_args = mock_add_positive.call_args[1]
     
                # Check the RSSItemSchema was created correctly
                rss_item = call_args['news']
                assert isinstance(rss_item, RSSItemSchema)
                assert rss_item.title == sample_news.title
                assert rss_item.link == sample_news.link


@pytest.mark.anyio
async def test_news_consumer_no_unprocessed_news():
    """Test news consumer when there are no unprocessed news items."""
    with patch.object(crud_news, 'get_unprocessed_news', return_value=[]):
        with patch.object(news_task_crud, 'get_active_tasks', return_value=[]):
            with patch.object(
                crud_prompt,
                'get_or_create',
                return_value=Prompt(role="test")
            ):
                # Should complete without errors
                await news_consumer()


@pytest.mark.anyio
async def test_news_consumer_with_relevant_news(
    sample_news, sample_news_task, sample_prompt
):
    """Test news consumer with unprocessed news and active tasks."""
    unprocessed_news = [sample_news]
    active_tasks = [sample_news_task]
    
    with patch.object(
        crud_news, 'get_unprocessed_news', return_value=unprocessed_news
    ):
        with patch.object(
            news_task_crud, 'get_active_tasks', return_value=active_tasks
        ):
            with patch.object(
                crud_prompt, 'get_or_create', return_value=sample_prompt
            ):
                with patch(
                    'ai_news_bot.ai.news_consumer.process_news',
                    return_value=True
                ) as mock_process:
                    with patch(
                        'ai_news_bot.ai.news_consumer.add_positive_news'
                    ) as mock_add_positive:
                        with patch.object(
                            crud_news, 'mark_news_as_processed'
                        ) as mock_mark_processed:
            
                            await news_consumer()

                            # Verify process_news was called
                            mock_process.assert_called_once()

                            # Verify add_positive_news was called
                            mock_add_positive.assert_called_once()

                            # Verify news was marked as processed
                            mock_mark_processed.assert_called_once()


@pytest.mark.anyio
async def test_news_consumer_with_not_relevant_news(
    sample_news, sample_news_task, sample_prompt
):
    """Test news consumer when news is not relevant to any task."""
    unprocessed_news = [sample_news]
    active_tasks = [sample_news_task]

    with patch.object(
        crud_news, 'get_unprocessed_news', return_value=unprocessed_news
    ):
        with patch.object(
            news_task_crud, 'get_active_tasks', return_value=active_tasks
        ):
            with patch.object(
                crud_prompt, 'get_or_create', return_value=sample_prompt
            ):
                with patch(
                    'ai_news_bot.ai.news_consumer.process_news',
                    return_value=False
                ) as mock_process:
                    with patch(
                        'ai_news_bot.ai.news_consumer.add_positive_news'
                    ) as mock_add_positive:
                        with patch.object(
                            crud_news, 'mark_news_as_processed'
                        ) as mock_mark_processed:
                            await news_consumer()  
                            # Verify process_news was called
                            mock_process.assert_called_once()
                            # Verify add_positive_news was NOT called
                            mock_add_positive.assert_not_called()
                            # Verify news was still marked as processed
                            mock_mark_processed.assert_called_once()
