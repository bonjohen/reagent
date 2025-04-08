"""
Tests for the truncation notification functionality in the research manager.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from research_agent.manager import ResearchManager
from research_agent.agents.planner_agent import WebSearchItem

@pytest.mark.asyncio
async def test_query_truncation_notification():
    """Test that query truncation is properly notified to the user."""
    # Create a manager instance
    manager = ResearchManager()

    # Create a mock printer
    mock_printer = MagicMock()
    manager.printer = mock_printer

    # Create a search item with a long query
    long_query = "a" * 300  # 300 characters, which exceeds the 200 character limit
    search_item = WebSearchItem(query=long_query, reason="test reason")

    # Mock the custom_search_tool to avoid making actual API calls
    mock_search_tool = MagicMock()
    mock_search_tool.search = AsyncMock(return_value="Test search result")

    # Patch the custom_search_tool
    with patch('research_agent.manager.custom_search_tool', mock_search_tool):
        # Call the _search method
        result = await manager._search(search_item)

        # Verify that the printer was updated with a warning
        mock_printer.update_item.assert_any_call(
            "warning",
            f"Query truncated due to excessive length: '{search_item.query[:200]}...'",
            is_done=True,
        )

        # Verify that the query was truncated
        assert len(search_item.query) == 200

        # Verify that the search result is as expected
        assert result == "Test search result"

@pytest.mark.asyncio
async def test_reason_truncation_notification():
    """Test that reason truncation is properly notified to the user."""
    # Create a manager instance
    manager = ResearchManager()

    # Create a mock printer
    mock_printer = MagicMock()
    manager.printer = mock_printer

    # Create a search item with a long reason
    long_reason = "a" * 600  # 600 characters, which exceeds the 500 character limit
    search_item = WebSearchItem(query="test query", reason=long_reason)

    # Mock the custom_search_tool to avoid making actual API calls
    mock_search_tool = MagicMock()
    mock_search_tool.search = AsyncMock(return_value="Test search result")

    # Patch the custom_search_tool
    with patch('research_agent.manager.custom_search_tool', mock_search_tool):
        # Call the _search method
        result = await manager._search(search_item)

        # Verify that the printer was updated with a warning
        mock_printer.update_item.assert_any_call(
            "warning",
            "Reason truncated due to excessive length",
            is_done=True,
        )

        # Verify that the reason was truncated
        assert len(search_item.reason) == 503  # 500 + 3 for "..."

        # Verify that the search result is as expected
        assert result == "Test search result"

@pytest.mark.asyncio
async def test_search_result_truncation_notification():
    """Test that search result truncation is properly notified to the user."""
    # Create a manager instance
    manager = ResearchManager()

    # Create a mock printer
    mock_printer = MagicMock()
    manager.printer = mock_printer

    # Create a search item
    search_item = WebSearchItem(query="test query", reason="test reason")

    # Create a mock for the custom_search_tool
    mock_search_tool = MagicMock()
    mock_search_tool.search = AsyncMock(return_value="a" * 6000)  # 6000 characters, which exceeds the 5000 character limit

    # Patch the custom_search_tool
    with patch('research_agent.manager.custom_search_tool', mock_search_tool):
        # Call the _search method
        result = await manager._search(search_item)

        # Verify that the printer was updated with a warning
        mock_printer.update_item.assert_any_call(
            "warning",
            f"Search result for 'test query' truncated from 6000 to 5000 characters",
            is_done=True,
        )

        # Verify that the result was truncated
        assert len(result) > 5000  # The result includes the truncation notice
        assert "[NOTICE: Result truncated due to excessive length" in result

        # Verify that the original length is mentioned in the result
        assert "Original length: 6000 characters" in result
