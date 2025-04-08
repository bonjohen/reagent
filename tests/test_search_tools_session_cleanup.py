"""
Tests for proper session cleanup in search tools.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from reagents.tools.search_tools import SerperSearchTool, TavilySearchTool

@pytest.mark.asyncio
async def test_serper_search_session_cleanup_on_success():
    """Test that the SerperSearchTool properly closes the session on success."""
    # Create a search tool instance
    search_tool = SerperSearchTool(api_key="test_key")
    
    # Create mocks for the aiohttp.ClientSession and its methods
    mock_session = MagicMock()
    mock_session.post = AsyncMock()
    mock_session.close = AsyncMock()
    
    # Create a mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"organic": []})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    
    # Configure the session.post to return the mock response
    mock_session.post.return_value = mock_response
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Call the search method
        result = await search_tool.search("test query")
        
        # Verify that the session was closed
        mock_session.close.assert_called_once()

@pytest.mark.asyncio
async def test_serper_search_session_cleanup_on_error():
    """Test that the SerperSearchTool properly closes the session on error."""
    # Create a search tool instance
    search_tool = SerperSearchTool(api_key="test_key")
    
    # Create mocks for the aiohttp.ClientSession and its methods
    mock_session = MagicMock()
    mock_session.post = AsyncMock(side_effect=Exception("Test exception"))
    mock_session.close = AsyncMock()
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Call the search method
        result = await search_tool.search("test query")
        
        # Verify that the session was closed
        mock_session.close.assert_called_once()

@pytest.mark.asyncio
async def test_tavily_search_session_cleanup_on_success():
    """Test that the TavilySearchTool properly closes the session on success."""
    # Create a search tool instance
    search_tool = TavilySearchTool(api_key="tvly-test_key")
    
    # Create mocks for the aiohttp.ClientSession and its methods
    mock_session = MagicMock()
    mock_session.get = AsyncMock()
    mock_session.close = AsyncMock()
    
    # Create a mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"results": []})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    
    # Configure the session.get to return the mock response
    mock_session.get.return_value = mock_response
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Call the search method
        result = await search_tool.search("test query")
        
        # Verify that the session was closed
        mock_session.close.assert_called_once()

@pytest.mark.asyncio
async def test_tavily_search_session_cleanup_on_error():
    """Test that the TavilySearchTool properly closes the session on error."""
    # Create a search tool instance
    search_tool = TavilySearchTool(api_key="tvly-test_key")
    
    # Create mocks for the aiohttp.ClientSession and its methods
    mock_session = MagicMock()
    mock_session.get = AsyncMock(side_effect=Exception("Test exception"))
    mock_session.close = AsyncMock()
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Call the search method
        result = await search_tool.search("test query")
        
        # Verify that the session was closed
        mock_session.close.assert_called_once()

@pytest.mark.asyncio
async def test_serper_search_session_cleanup_on_response_error():
    """Test that the SerperSearchTool properly closes the session when the response has an error status."""
    # Create a search tool instance
    search_tool = SerperSearchTool(api_key="test_key")
    
    # Create mocks for the aiohttp.ClientSession and its methods
    mock_session = MagicMock()
    mock_session.post = AsyncMock()
    mock_session.close = AsyncMock()
    
    # Create a mock response with an error status
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.text = AsyncMock(return_value="Bad Request")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    
    # Configure the session.post to return the mock response
    mock_session.post.return_value = mock_response
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Call the search method
        result = await search_tool.search("test query")
        
        # Verify that the session was closed
        mock_session.close.assert_called_once()

@pytest.mark.asyncio
async def test_tavily_search_session_cleanup_on_response_error():
    """Test that the TavilySearchTool properly closes the session when the response has an error status."""
    # Create a search tool instance
    search_tool = TavilySearchTool(api_key="tvly-test_key")
    
    # Create mocks for the aiohttp.ClientSession and its methods
    mock_session = MagicMock()
    mock_session.get = AsyncMock()
    mock_session.close = AsyncMock()
    
    # Create a mock response with an error status
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.text = AsyncMock(return_value="Bad Request")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    
    # Configure the session.get to return the mock response
    mock_session.get.return_value = mock_response
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Call the search method
        result = await search_tool.search("test query")
        
        # Verify that the session was closed
        mock_session.close.assert_called_once()
