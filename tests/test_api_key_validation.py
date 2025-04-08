"""
Tests for API key validation in search tools.
"""

import pytest
import logging
from unittest.mock import patch
from research_agent.tools.search_tools import SerperSearchTool, TavilySearchTool

def test_serper_api_key_validation_valid():
    """Test that a valid Serper API key passes validation."""
    with patch('research_agent.tools.search_tools.logger') as mock_logger:
        # Valid key (32 chars, alphanumeric)
        api_key = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
        search_tool = SerperSearchTool(api_key=api_key)
        
        # No warnings should be logged
        mock_logger.warning.assert_not_called()

def test_serper_api_key_validation_too_short():
    """Test that a too-short Serper API key triggers a warning."""
    with patch('research_agent.tools.search_tools.logger') as mock_logger:
        # Too short key
        api_key = "tooshort"
        search_tool = SerperSearchTool(api_key=api_key)
        
        # Warning should be logged about length
        mock_logger.warning.assert_called_with(f"Serper API key appears to be too short: {len(api_key)} chars")

def test_serper_api_key_validation_invalid_chars():
    """Test that a Serper API key with invalid characters triggers a warning."""
    with patch('research_agent.tools.search_tools.logger') as mock_logger:
        # Key with invalid characters
        api_key = "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6"
        search_tool = SerperSearchTool(api_key=api_key)
        
        # Warning should be logged about invalid characters
        mock_logger.warning.assert_called_with("Serper API key contains non-alphanumeric characters")

def test_tavily_api_key_validation_valid():
    """Test that a valid Tavily API key passes validation."""
    with patch('research_agent.tools.search_tools.logger') as mock_logger:
        # Valid key (starts with tvly-, followed by alphanumeric)
        api_key = "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"
        search_tool = TavilySearchTool(api_key=api_key)
        
        # No warnings should be logged
        mock_logger.warning.assert_not_called()

def test_tavily_api_key_validation_missing_prefix():
    """Test that a Tavily API key without the tvly- prefix triggers a warning."""
    with patch('research_agent.tools.search_tools.logger') as mock_logger:
        # Key without tvly- prefix
        api_key = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
        search_tool = TavilySearchTool(api_key=api_key)
        
        # Warning should be logged about missing prefix
        mock_logger.warning.assert_called_with("Tavily API key does not start with 'tvly-' prefix")

def test_tavily_api_key_validation_too_short():
    """Test that a too-short Tavily API key triggers a warning."""
    with patch('research_agent.tools.search_tools.logger') as mock_logger:
        # Too short key
        api_key = "tvly-tooshort"
        search_tool = TavilySearchTool(api_key=api_key)
        
        # Warning should be logged about length
        mock_logger.warning.assert_called_with(f"Tavily API key appears to be too short: {len(api_key)} chars")

def test_tavily_api_key_validation_invalid_chars():
    """Test that a Tavily API key with invalid characters triggers a warning."""
    with patch('research_agent.tools.search_tools.logger') as mock_logger:
        # Key with invalid characters
        api_key = "tvly-a1b2c3d4-e5f6-g7h8-i9j0"
        search_tool = TavilySearchTool(api_key=api_key)
        
        # Warning should be logged about invalid characters
        mock_logger.warning.assert_called_with("Tavily API key contains invalid characters")
