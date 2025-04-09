"""
Tests for the JSON error recovery functionality in the planner agent.
"""

from reagents.agents.planner_agent import WebSearchPlan

def test_empty_fallback_plan():
    """Test that the fallback plan is empty when JSON parsing fails."""
    # Create an invalid JSON response
    invalid_json = """
    {
        "searches": [
            {"query": "climate change agriculture", "reason": "Basic overview"},
            {"query": "global warming effects on crops", "reason": "Specific impacts"}
        ]
    """  # Missing closing brace

    # Parse the response
    search_plan = WebSearchPlan.from_response(invalid_json)

    # Verify that the fallback plan is empty
    assert len(search_plan.searches) == 0  # Should have no search items

def test_fallback_plan_with_invalid_json():
    """Test that the fallback plan is empty with completely invalid JSON."""
    # Create an invalid JSON response
    invalid_json = "This is not JSON at all"

    # Parse the response
    search_plan = WebSearchPlan.from_response(invalid_json)

    # Verify that the fallback plan is empty
    assert len(search_plan.searches) == 0  # Should have no search items

def test_fallback_plan_with_missing_searches():
    """Test that the fallback plan is empty when the searches field is missing."""
    # Create a JSON response with missing searches field
    invalid_json = '{"not_searches": []}'

    # Parse the response
    search_plan = WebSearchPlan.from_response(invalid_json)

    # Verify that the fallback plan is empty
    assert len(search_plan.searches) == 0  # Should have no search items
