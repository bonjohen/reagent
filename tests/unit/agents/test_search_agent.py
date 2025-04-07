"""
Unit tests for the search_agent module.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from research_agent.agents.search_agent import EnhancedWebSearchTool


class TestSearchAgent:
    """Tests for the search_agent module."""

    @pytest.mark.asyncio
    async def test_enhanced_web_search_tool_success(self):
        """Test the EnhancedWebSearchTool with a successful search."""
        # Create a mock for the parent class's _run method
        with patch.object(EnhancedWebSearchTool, '__init__', return_value=None), \
             patch.object(EnhancedWebSearchTool, '_run', new_callable=AsyncMock) as mock_run:
            
            # Configure the mock to return a successful result
            mock_run.return_value = "Test search result"
            
            # Create an instance of the tool
            tool = EnhancedWebSearchTool()
            
            # Call the _run method
            result = await tool._run("test query")
            
            # Check that the parent's _run method was called
            mock_run.assert_called_once_with("test query")
            
            # Check the result
            assert result == "Test search result"

    @pytest.mark.asyncio
    async def test_enhanced_web_search_tool_empty_result(self):
        """Test the EnhancedWebSearchTool with an empty result."""
        # Create a mock for the parent class's _run method
        with patch.object(EnhancedWebSearchTool, '__init__', return_value=None), \
             patch.object(EnhancedWebSearchTool, '_run', new_callable=AsyncMock) as mock_run:
            
            # Configure the mock to return an empty result
            mock_run.return_value = ""
            
            # Create an instance of the tool
            tool = EnhancedWebSearchTool()
            
            # Call the _run method
            result = await tool._run("test query")
            
            # Check that the parent's _run method was called
            mock_run.assert_called_once_with("test query")
            
            # Check the result - should be a message about no results
            assert "No results found" in result

    @pytest.mark.asyncio
    async def test_enhanced_web_search_tool_exception(self):
        """Test the EnhancedWebSearchTool with an exception."""
        # Create a mock for the parent class's _run method
        with patch.object(EnhancedWebSearchTool, '__init__', return_value=None), \
             patch.object(EnhancedWebSearchTool, '_run', new_callable=AsyncMock) as mock_run:
            
            # Configure the mock to raise an exception
            mock_run.side_effect = Exception("Test exception")
            
            # Create an instance of the tool
            tool = EnhancedWebSearchTool()
            
            # Call the _run method
            result = await tool._run("test query")
            
            # Check that the parent's _run method was called
            mock_run.assert_called_once_with("test query")
            
            # Check the result - should be an error message
            assert "Error performing web search" in result
            assert "Test exception" in result

    @pytest.mark.asyncio
    async def test_enhanced_web_search_tool_logging(self):
        """Test that the EnhancedWebSearchTool logs properly."""
        # Create a mock for the parent class's _run method and for the logger
        with patch.object(EnhancedWebSearchTool, '__init__', return_value=None), \
             patch.object(EnhancedWebSearchTool, '_run', new_callable=AsyncMock), \
             patch('research_agent.agents.search_agent.logger') as mock_logger:
            
            # Create an instance of the tool
            tool = EnhancedWebSearchTool()
            
            # Call the _run method
            await tool._run("test query")
            
            # Check that the logger was called
            mock_logger.info.assert_called_once_with("Performing web search for: test query")
