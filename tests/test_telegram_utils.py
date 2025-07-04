"""Tests for telegram utils module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from ai_news_bot.telegram.utils import parse_rsss_item


@pytest.mark.parametrize(
    "message_text,expected_result",
    [
        # Case 1: Complete message with all fields
        (
            "News: Test headline\n"
            "Description: Test description\n"
            "Link: https://example.com/test",
            {
                "title": "Test headline",
                "description": "Test description",
                "link": "https://example.com/test",
            },
        ),
        # Case 2: Message with Russian text
        (
            "News: Эксперт: российские компании используют B2B-платформы\n"
            "Link: https://example.ru/test\n"
            "Description: В России закупки через платформы растут быстро",
            {
                "title": "Эксперт: российские компании используют B2B-платформы",
                "description": "В России закупки через платформы растут быстро",
                "link": "https://example.ru/test",
            },
        ),
        # Case 3: Message with missing description
        (
            "News: Another headline\nLink: https://example.com/another",
            {
                "title": "Another headline",
                "link": "https://example.com/another",
                "description": None,  # Description is missing
            },
        ),
        # Case 4: Message with special characters in title
        (
            "News: Title with: special characters!\n"
            "Link: https://example.com/special\n"
            "Description: Some description",
            {
                "title": "Title with: special characters!",
                "description": "Some description",
                "link": "https://example.com/special",
            },
        ),
        # Case 5: Different order of elements
        (
            "Link: https://example.com/order\n"
            "News: Test order\n"
            "Description: Different order",
            {
                "title": "Test order",
                "description": "Different order",
                "link": "https://example.com/order",
            },
        ),
    ],
)
def test_parse_rsss_item(message_text, expected_result):
    """Test the function to parse RSS items from message text."""
    # Create a mock CallbackQuery object
    message_mock = MagicMock()
    message_mock.text = message_text
    test_date = datetime(2025, 6, 8, 12, 0, 0)  # Fixed test date
    message_mock.date = test_date

    query_mock = MagicMock()
    query_mock.message = message_mock

    # Mock the RSSItemSchema to accept partial data for testing
    with patch("ai_news_bot.telegram.utils.RSSItemSchema") as mock_schema:
        # Call the function
        parse_rsss_item(query_mock)

        # Verify schema was called with expected args
        assert mock_schema.called
        _, call_kwargs = mock_schema.call_args

        # Check for expected fields from the message
        if "title" in expected_result:
            assert call_kwargs.get("title") == expected_result["title"]
        if "description" in expected_result:
            assert call_kwargs.get("description") == expected_result["description"]
        if "link" in expected_result:
            assert call_kwargs.get("link") == expected_result["link"]
        assert call_kwargs.get("pub_date") == test_date


def test_parse_rsss_item_none_message():
    """Test the function with a None message."""
    query_mock = MagicMock()
    query_mock.message = None

    result = parse_rsss_item(query_mock)
    assert result is None


def test_parse_rsss_item_empty_message():
    """Test the function with an empty message."""
    message_mock = MagicMock()
    message_mock.text = ""

    query_mock = MagicMock()
    query_mock.message = message_mock

    result = parse_rsss_item(query_mock)
    assert result is None


def test_parse_rsss_item_missing_all_fields():
    """Test with a message missing all expected fields."""
    message_mock = MagicMock()
    message_mock.text = "Some random text without any recognizable fields"
    message_mock.date = datetime(2025, 6, 8, 12, 0, 0)

    query_mock = MagicMock()
    query_mock.message = message_mock

    # Mock the schema since we expect it to be called with missing required fields
    with patch("ai_news_bot.telegram.utils.RSSItemSchema") as mock_schema:
        parse_rsss_item(query_mock)

        # Verify what fields would be passed to the schema
        _, call_kwargs = mock_schema.call_args

        # Should only contain pub_date, as other fields weren't found
        assert "pub_date" in call_kwargs
        assert call_kwargs["pub_date"] == message_mock.date
        assert "title" not in call_kwargs
        assert "link" not in call_kwargs
        assert "description" not in call_kwargs


def test_parse_rsss_item_missing_title():
    """Test with a message missing the required title field."""
    message_mock = MagicMock()
    message_mock.text = "Link: https://example.com\nDescription: Test"
    message_mock.date = datetime(2025, 6, 8, 12, 0, 0)

    query_mock = MagicMock()
    query_mock.message = message_mock

    with patch("ai_news_bot.telegram.utils.RSSItemSchema") as mock_schema:
        # In a real scenario this would fail due to missing title
        # But we mock the schema to test parsing logic
        parse_rsss_item(query_mock)

        # Verify the extracted fields
        _, call_kwargs = mock_schema.call_args
        assert "pub_date" in call_kwargs
        assert "link" in call_kwargs
        assert "description" in call_kwargs
        assert "title" not in call_kwargs


def test_parse_rsss_item_with_extra_newlines():
    """Test with a message containing extra newlines between fields."""
    message_mock = MagicMock()
    message_mock.text = (
        "News: Test headline\n\n"
        "Description: Test description\n\n"
        "Link: https://example.com/test"
    )
    message_mock.date = datetime(2025, 6, 8, 12, 0, 0)

    query_mock = MagicMock()
    query_mock.message = message_mock

    with patch("ai_news_bot.telegram.utils.RSSItemSchema") as mock_schema:
        parse_rsss_item(query_mock)

        # Verify fields were correctly extracted despite extra newlines
        _, call_kwargs = mock_schema.call_args
        assert call_kwargs.get("title") == "Test headline"
        assert call_kwargs.get("description") == "Test description"
        assert call_kwargs.get("link") == "https://example.com/test"


def test_parse_rsss_item_validation_error() -> None:
    """Test behavior when RSSItemSchema validation fails."""
    message_mock = MagicMock()
    message_mock.text = "News: Test headline"
    message_mock.date = datetime(2025, 6, 8, 12, 0, 0)

    query_mock = MagicMock()
    query_mock.message = message_mock

    with patch("ai_news_bot.telegram.utils.RSSItemSchema") as mock_schema:
        # Make the schema raise an exception when instantiated
        mock_schema.side_effect = ValueError("Missing required field")

        # The function should handle the error gracefully and return None
        result = parse_rsss_item(query_mock)
        assert result is None
