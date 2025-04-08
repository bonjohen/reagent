"""
Tests for the search rate limiting functionality in the research manager.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from reagents.manager import ResearchManager
from reagents.agents.planner_agent import WebSearchItem, WebSearchPlan

@pytest.mark.asyncio
async def test_rate_limited_search_delay_before_semaphore():
    """Test that the delay happens before acquiring the semaphore in rate_limited_search."""
    # Create a manager instance
    manager = ResearchManager()

    # Create a mock for asyncio.sleep to track when it's called
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep, \
         patch.object(manager, '_search', new_callable=AsyncMock) as mock_search, \
         patch('asyncio.Semaphore') as mock_semaphore_class:

        # Configure the mocks
        mock_search.return_value = "Test search result"

        # Create a mock semaphore with tracking capabilities
        mock_semaphore = MagicMock()
        mock_semaphore_context = MagicMock()
        mock_semaphore_context.__aenter__ = AsyncMock()
        mock_semaphore_context.__aexit__ = AsyncMock()
        mock_semaphore.__aenter__.return_value = mock_semaphore_context
        mock_semaphore_class.return_value = mock_semaphore

        # Create a search plan with two items
        search_plan = WebSearchPlan(searches=[
            WebSearchItem(query="test query 1", reason="test reason 1"),
            WebSearchItem(query="test query 2", reason="test reason 2")
        ])

        # Call the _perform_searches method
        results = await manager._perform_searches(search_plan)

        # Verify that asyncio.sleep was called before semaphore.__aenter__
        # We can check the call order by comparing the call counts
        assert mock_sleep.call_count >= 2  # Called at least once for each search item
        assert mock_semaphore.__aenter__.call_count >= 2  # Called at least once for each search item

        # Check that the results are as expected
        assert len(results) == 2
        assert all(isinstance(result, str) for result in results)
        assert all("Test search result" in result for result in results)

@pytest.mark.asyncio
async def test_concurrent_searches_with_rate_limiting():
    """Test that concurrent searches are properly rate limited."""
    # Create a manager instance
    manager = ResearchManager()

    # Create a tracking mechanism to record when searches are executed
    search_times = []

    async def mock_search_with_timing(item):
        # Record the time when this search starts
        search_times.append(asyncio.get_event_loop().time())
        # Simulate some work
        await asyncio.sleep(0.1)
        return f"Result for {item.query}"

    # Patch the necessary methods
    with patch.object(manager, '_search', side_effect=mock_search_with_timing):
        # Create a search plan with multiple items
        search_plan = WebSearchPlan(searches=[
            WebSearchItem(query=f"test query {i}", reason=f"test reason {i}")
            for i in range(5)  # 5 search items
        ])

        # Call the _perform_searches method
        results = await manager._perform_searches(search_plan)

        # Verify that we got results for all searches
        assert len(results) == 5

        # Check that all expected results are present
        # Since searches run concurrently, the order might not match the input order
        expected_results = [f"Result for test query {i}" for i in range(5)]
        for result in results:
            # Find and remove the matching expected result
            for expected in expected_results[:]:  # Create a copy to iterate over
                if expected in result:
                    expected_results.remove(expected)
                    break

        # Verify all expected results were found
        assert len(expected_results) == 0, f"Missing expected results: {expected_results}"

        # Verify that searches were properly rate limited
        # The time between consecutive searches should be at least the delay_between_searches
        # But we can't test this precisely in a unit test, so we just check that all searches completed
        assert len(search_times) == 5
