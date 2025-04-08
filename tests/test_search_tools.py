"""
Tests for the search tools with size limits.
"""

import pytest
from unittest.mock import patch, MagicMock
from research_agent.tools.search_tools import SerperSearchTool, TavilySearchTool

def test_serper_format_results_with_size_limits():
    """Test that SerperSearchTool._format_results respects size limits."""
    search_tool = SerperSearchTool()
    
    # Create a mock response with a lot of data
    mock_data = {
        "organic": [
            {
                "title": "Title " + ("very long " * 20),  # Long title
                "link": "https://example.com/1",
                "snippet": "Snippet " + ("very long " * 50)  # Very long snippet
            },
            # Add more results to exceed the limit
            {"title": "Title 2", "link": "https://example.com/2", "snippet": "Snippet 2"},
            {"title": "Title 3", "link": "https://example.com/3", "snippet": "Snippet 3"},
            {"title": "Title 4", "link": "https://example.com/4", "snippet": "Snippet 4"},
            {"title": "Title 5", "link": "https://example.com/5", "snippet": "Snippet 5"},
            {"title": "Title 6", "link": "https://example.com/6", "snippet": "Snippet 6"},
            {"title": "Title 7", "link": "https://example.com/7", "snippet": "Snippet 7"},
            {"title": "Title 8", "link": "https://example.com/8", "snippet": "Snippet 8"},
            {"title": "Title 9", "link": "https://example.com/9", "snippet": "Snippet 9"},
            {"title": "Title 10", "link": "https://example.com/10", "snippet": "Snippet 10"}
        ],
        "knowledgeGraph": {
            "title": "Knowledge Graph Title",
            "description": "Knowledge Graph Description"
        },
        "relatedSearches": [
            "Related search 1",
            "Related search 2",
            "Related search 3",
            "Related search 4",
            "Related search 5",
            "Related search 6"  # This one should be truncated
        ]
    }
    
    # Test with a small max_chars limit
    result = search_tool._format_results(mock_data, "test query", max_chars=500)
    
    # Check that the result is truncated
    assert len(result) <= 500 + 100  # Allow some buffer for the truncation notice
    assert "[Note: Search results were truncated" in result
    
    # Check that the first title is truncated
    assert "..." in result
    
    # Test with a larger limit that should include everything
    result = search_tool._format_results(mock_data, "test query", max_chars=10000)
    
    # Check that all results are included
    for i in range(1, 11):
        assert f"Title {i}" in result or f"Title {i-1}" in result  # Account for the first title being different
    
    # Check that related searches are limited to 5
    assert "Related search 5" in result
    assert "Related search 6" not in result

def test_tavily_format_results_with_size_limits():
    """Test that TavilySearchTool._format_results respects size limits."""
    search_tool = TavilySearchTool()
    
    # Create a mock response with a lot of data
    mock_data = {
        "answer": "Answer " + ("very long " * 100),  # Very long answer
        "results": [
            {
                "title": "Title " + ("very long " * 20),  # Long title
                "url": "https://example.com/1",
                "content": "Content " + ("very long " * 50)  # Very long content
            },
            # Add more results to exceed the limit
            {"title": "Title 2", "url": "https://example.com/2", "content": "Content 2"},
            {"title": "Title 3", "url": "https://example.com/3", "content": "Content 3"},
            {"title": "Title 4", "url": "https://example.com/4", "content": "Content 4"},
            {"title": "Title 5", "url": "https://example.com/5", "content": "Content 5"},
            {"title": "Title 6", "url": "https://example.com/6", "content": "Content 6"},
            {"title": "Title 7", "url": "https://example.com/7", "content": "Content 7"},
            {"title": "Title 8", "url": "https://example.com/8", "content": "Content 8"},
            {"title": "Title 9", "url": "https://example.com/9", "content": "Content 9"},
            {"title": "Title 10", "url": "https://example.com/10", "content": "Content 10"}
        ]
    }
    
    # Test with a small max_chars limit
    result = search_tool._format_results(mock_data, "test query", max_chars=500)
    
    # Check that the result is truncated
    assert len(result) <= 500 + 100  # Allow some buffer for the truncation notice
    assert "[Note: Search results were truncated" in result
    
    # Check that the answer is truncated
    assert "..." in result
    
    # Test with a larger limit that should include everything
    result = search_tool._format_results(mock_data, "test query", max_chars=10000)
    
    # Check that all results are included
    for i in range(1, 11):
        assert f"Title {i}" in result or f"Title {i-1}" in result  # Account for the first title being different
