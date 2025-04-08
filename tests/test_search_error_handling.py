"""
Tests for search error handling in the research manager.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from research_agent.manager import ResearchManager
from research_agent.agents.planner_agent import WebSearchItem

@pytest.mark.asyncio
async def test_search_with_non_string_result():
    """Test that _perform_searches handles non-string results correctly."""
    # Create a mock for the _search method that returns a dictionary instead of a string
    with patch.object(ResearchManager, '_search', new_callable=AsyncMock) as mock_search:
        # Configure the mock to return a dictionary (which is not a string)
        mock_search.return_value = {"error": "This is a dictionary, not a string"}
        
        # Create a manager instance
        manager = ResearchManager()
        
        # Create a mock search plan
        mock_search_plan = MagicMock()
        mock_search_plan.searches = [
            WebSearchItem(query="test query", reason="test reason")
        ]
        
        # Call the _perform_searches method
        results = await manager._perform_searches(mock_search_plan)
        
        # Check that the result is a list of strings
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], str)
        assert "expected str instance, dict found" in results[0]

@pytest.mark.asyncio
async def test_search_with_exception():
    """Test that _perform_searches handles exceptions correctly."""
    # Create a mock for the _search method that raises an exception
    with patch.object(ResearchManager, '_search', new_callable=AsyncMock) as mock_search:
        # Configure the mock to raise an exception
        mock_search.side_effect = ValueError("Test exception")
        
        # Create a manager instance
        manager = ResearchManager()
        
        # Create a mock search plan
        mock_search_plan = MagicMock()
        mock_search_plan.searches = [
            WebSearchItem(query="test query", reason="test reason")
        ]
        
        # Call the _perform_searches method
        results = await manager._perform_searches(mock_search_plan)
        
        # Check that the result is a list of strings
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], str)
        assert "Search error" in results[0]
        assert "Test exception" in results[0]
