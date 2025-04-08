"""
Tests for the improved search tools with robust error handling.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from reagents.tools.search_tools import SerperSearchTool, TavilySearchTool

@pytest.mark.asyncio
async def test_serper_search_with_invalid_data():
    """Test that SerperSearchTool.search handles invalid data correctly."""
    search_tool = SerperSearchTool(api_key="test_key")
    
    # Mock the aiohttp.ClientSession to return invalid data
    with patch("aiohttp.ClientSession") as mock_session:
        # Create mock for the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=["This is a list, not a dict"])
        
        # Configure the context managers
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.__aexit__.return_value = None
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        
        mock_session.return_value = mock_session_instance
        
        # Call the search method
        result = await search_tool.search("test query")
        
        # Check that the result contains an error message
        assert "Search error: Serper API returned non-dictionary data" in result

@pytest.mark.asyncio
async def test_serper_search_with_invalid_organic_results():
    """Test that SerperSearchTool.search handles invalid organic results correctly."""
    search_tool = SerperSearchTool(api_key="test_key")
    
    # Mock the aiohttp.ClientSession to return data with invalid organic results
    with patch("aiohttp.ClientSession") as mock_session:
        # Create mock for the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"organic": "This is a string, not a list"})
        
        # Configure the context managers
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.__aexit__.return_value = None
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        
        mock_session.return_value = mock_session_instance
        
        # Call the search method
        result = await search_tool.search("test query")
        
        # Check that the result contains an error message
        assert "Error: Serper API returned non-list organic results" in result

@pytest.mark.asyncio
async def test_serper_search_with_invalid_organic_item():
    """Test that SerperSearchTool.search handles invalid items in organic results correctly."""
    search_tool = SerperSearchTool(api_key="test_key")
    
    # Mock the aiohttp.ClientSession to return data with invalid items in organic results
    with patch("aiohttp.ClientSession") as mock_session:
        # Create mock for the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"organic": [123, {"title": "Valid Item"}]})
        
        # Configure the context managers
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.__aexit__.return_value = None
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        
        mock_session.return_value = mock_session_instance
        
        # Call the search method
        result = await search_tool.search("test query")
        
        # Check that the result contains the valid item
        assert "Valid Item" in result

@pytest.mark.asyncio
async def test_tavily_search_with_invalid_data():
    """Test that TavilySearchTool.search handles invalid data correctly."""
    search_tool = TavilySearchTool(api_key="tvly-test_key")
    
    # Mock the aiohttp.ClientSession to return invalid data
    with patch("aiohttp.ClientSession") as mock_session:
        # Create mock for the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=["This is a list, not a dict"])
        
        # Configure the context managers
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.__aexit__.return_value = None
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        
        mock_session.return_value = mock_session_instance
        
        # Call the search method
        result = await search_tool.search("test query")
        
        # Check that the result contains an error message
        assert "Search error: Tavily API returned non-dictionary data" in result

@pytest.mark.asyncio
async def test_tavily_search_with_invalid_results():
    """Test that TavilySearchTool.search handles invalid results correctly."""
    search_tool = TavilySearchTool(api_key="tvly-test_key")
    
    # Mock the aiohttp.ClientSession to return data with invalid results
    with patch("aiohttp.ClientSession") as mock_session:
        # Create mock for the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"results": "This is a string, not a list"})
        
        # Configure the context managers
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.__aexit__.return_value = None
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        
        mock_session.return_value = mock_session_instance
        
        # Call the search method
        result = await search_tool.search("test query")
        
        # Check that the result contains an error message
        assert "Error: Tavily API returned non-list results" in result
