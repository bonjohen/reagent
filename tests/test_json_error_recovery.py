"""
Tests for the JSON error recovery functionality in the planner agent.
"""

import pytest
from reagents.agents.planner_agent import WebSearchPlan

def test_fallback_plan_preserves_query_intent():
    """Test that the fallback plan preserves the original query intent."""
    # Test with a valid original query
    original_query = "climate change impacts on agriculture"
    
    # Create an invalid JSON response
    invalid_json = """
    {
        "searches": [
            {"query": "climate change agriculture", "reason": "Basic overview"},
            {"query": "global warming effects on crops", "reason": "Specific impacts"}
        ]
    """  # Missing closing brace
    
    # Parse the response with the original query
    search_plan = WebSearchPlan.from_response(invalid_json, original_query=original_query)
    
    # Verify that the fallback plan includes the original query
    assert len(search_plan.searches) >= 3  # Should have at least 3 search items
    
    # Check that the first search item is the original query
    assert search_plan.searches[0].query == original_query
    assert "original query" in search_plan.searches[0].reason.lower()
    
    # Check that other search items are variations of the original query
    for item in search_plan.searches[1:]:
        assert isinstance(item.query, str)
        assert isinstance(item.reason, str)
        # At least one of the search items should contain "latest research"
        if "latest research" in item.query:
            assert original_query in item.query
            break
    else:
        assert False, "No search item with 'latest research' found"

def test_fallback_plan_with_long_query():
    """Test that the fallback plan handles long queries correctly."""
    # Test with a long original query
    original_query = "what are the economic and environmental impacts of renewable energy adoption in developing countries compared to developed nations"
    
    # Create an invalid JSON response
    invalid_json = "This is not JSON at all"
    
    # Parse the response with the original query
    search_plan = WebSearchPlan.from_response(invalid_json, original_query=original_query)
    
    # Verify that the fallback plan includes the original query
    assert len(search_plan.searches) >= 3  # Should have at least 3 search items
    
    # Check that the first search item is the original query
    assert search_plan.searches[0].query == original_query
    
    # Check that there's a focused search with just the first 3 words
    first_three_words = " ".join(original_query.split()[:3])
    for item in search_plan.searches:
        if first_three_words in item.query and "guide" in item.query:
            assert "main topic" in item.reason.lower()
            break
    else:
        assert False, "No focused search with first 3 words found"

def test_fallback_plan_without_original_query():
    """Test that the fallback plan works even without an original query."""
    # Create an invalid JSON response
    invalid_json = "Not JSON"
    
    # Parse the response without an original query
    search_plan = WebSearchPlan.from_response(invalid_json)
    
    # Verify that the fallback plan includes generic searches
    assert len(search_plan.searches) >= 2  # Should have at least 2 search items
    
    # Check that the search items are the generic fallback searches
    assert any("error in search plan generation" in item.query for item in search_plan.searches)
    assert any("basic research methodology" in item.query for item in search_plan.searches)
