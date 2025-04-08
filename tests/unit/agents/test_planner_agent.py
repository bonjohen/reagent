"""
Unit tests for the planner_agent module.
"""
import pytest
import json
import re
from unittest.mock import patch

from reagents.agents.planner_agent import WebSearchItem, WebSearchPlan


class TestPlannerAgent:
    """Tests for the planner_agent module."""

    def test_web_search_item_model(self):
        """Test the WebSearchItem model."""
        # Create a WebSearchItem instance
        item = WebSearchItem(
            query="test query",
            reason="test reason"
        )
        
        # Check the fields
        assert item.query == "test query"
        assert item.reason == "test reason"

    def test_web_search_plan_model(self):
        """Test the WebSearchPlan model."""
        # Create a WebSearchPlan instance
        plan = WebSearchPlan(
            searches=[
                WebSearchItem(query="query 1", reason="reason 1"),
                WebSearchItem(query="query 2", reason="reason 2")
            ]
        )
        
        # Check the fields
        assert len(plan.searches) == 2
        assert plan.searches[0].query == "query 1"
        assert plan.searches[0].reason == "reason 1"
        assert plan.searches[1].query == "query 2"
        assert plan.searches[1].reason == "reason 2"

    def test_from_response_json_format(self):
        """Test parsing a JSON response."""
        # Create a JSON response
        response_data = {
            "searches": [
                {"query": "query 1", "reason": "reason 1"},
                {"query": "query 2", "reason": "reason 2"}
            ]
        }
        response = json.dumps(response_data)
        
        # Parse the response
        plan = WebSearchPlan.from_response(response)
        
        # Check the parsed data
        assert len(plan.searches) == 2
        assert plan.searches[0].query == "query 1"
        assert plan.searches[0].reason == "reason 1"
        assert plan.searches[1].query == "query 2"
        assert plan.searches[1].reason == "reason 2"

    def test_from_response_markdown_json_format(self):
        """Test parsing a JSON response wrapped in markdown code blocks."""
        # Create a JSON response wrapped in markdown
        response_data = {
            "searches": [
                {"query": "query 1", "reason": "reason 1"},
                {"query": "query 2", "reason": "reason 2"}
            ]
        }
        response = f"```json\n{json.dumps(response_data)}\n```"
        
        # Parse the response
        plan = WebSearchPlan.from_response(response)
        
        # Check the parsed data
        assert len(plan.searches) == 2
        assert plan.searches[0].query == "query 1"
        assert plan.searches[0].reason == "reason 1"
        assert plan.searches[1].query == "query 2"
        assert plan.searches[1].reason == "reason 2"

    def test_from_response_code_block_format(self):
        """Test parsing a JSON response wrapped in generic code blocks."""
        # Create a JSON response wrapped in generic code blocks
        response_data = {
            "searches": [
                {"query": "query 1", "reason": "reason 1"},
                {"query": "query 2", "reason": "reason 2"}
            ]
        }
        response = f"```\n{json.dumps(response_data)}\n```"
        
        # Parse the response
        plan = WebSearchPlan.from_response(response)
        
        # Check the parsed data
        assert len(plan.searches) == 2
        assert plan.searches[0].query == "query 1"
        assert plan.searches[0].reason == "reason 1"
        assert plan.searches[1].query == "query 2"
        assert plan.searches[1].reason == "reason 2"

    def test_from_response_invalid_json(self):
        """Test parsing an invalid JSON response."""
        # Create an invalid JSON response
        response = "This is not valid JSON"
        
        # Parse the response - should create a fallback plan
        plan = WebSearchPlan.from_response(response)
        
        # Check that a fallback plan was created
        assert len(plan.searches) > 0
        assert "error" in plan.searches[0].query.lower() or "error" in plan.searches[0].reason.lower()

    def test_from_response_missing_searches(self):
        """Test parsing a JSON response with missing searches field."""
        # Create a JSON response with missing searches field
        response_data = {
            "other_field": "value"
            # Missing searches field
        }
        response = json.dumps(response_data)
        
        # Parse the response - should create a fallback plan
        plan = WebSearchPlan.from_response(response)
        
        # Check that a fallback plan was created
        assert len(plan.searches) > 0
        assert "error" in plan.searches[0].query.lower() or "error" in plan.searches[0].reason.lower()

    def test_from_response_invalid_searches_type(self):
        """Test parsing a JSON response with searches not being a list."""
        # Create a JSON response with searches not being a list
        response_data = {
            "searches": "not a list"
        }
        response = json.dumps(response_data)
        
        # Parse the response - should create a fallback plan
        plan = WebSearchPlan.from_response(response)
        
        # Check that a fallback plan was created
        assert len(plan.searches) > 0
        assert "error" in plan.searches[0].query.lower() or "error" in plan.searches[0].reason.lower()

    def test_from_response_invalid_search_item(self):
        """Test parsing a JSON response with invalid search items."""
        # Create a JSON response with invalid search items
        response_data = {
            "searches": [
                "not an object",
                {"missing_query": "value"},
                {"query": "valid query", "missing_reason": "value"}
            ]
        }
        response = json.dumps(response_data)
        
        # Parse the response - should create a fallback plan
        plan = WebSearchPlan.from_response(response)
        
        # Check that a fallback plan was created
        assert len(plan.searches) > 0
        assert "error" in plan.searches[0].query.lower() or "error" in plan.searches[0].reason.lower()

    def test_json_repair(self):
        """Test the JSON repair functionality."""
        # Test various common JSON errors
        
        # Single quotes instead of double quotes
        invalid_json = "{'searches': [{'query': 'query 1', 'reason': 'reason 1'}]}"
        repaired = WebSearchPlan._attempt_json_repair(invalid_json)
        # Should be valid JSON now
        data = json.loads(repaired)
        assert "searches" in data
        assert len(data["searches"]) == 1
        assert data["searches"][0]["query"] == "query 1"
        
        # Unquoted keys
        invalid_json = "{searches: [{query: \"query 1\", reason: \"reason 1\"}]}"
        repaired = WebSearchPlan._attempt_json_repair(invalid_json)
        # Should be valid JSON now
        data = json.loads(repaired)
        assert "searches" in data
        assert len(data["searches"]) == 1
        assert data["searches"][0]["query"] == "query 1"
        
        # Trailing commas
        invalid_json = "{\"searches\": [{\"query\": \"query 1\", \"reason\": \"reason 1\", }]}"
        repaired = WebSearchPlan._attempt_json_repair(invalid_json)
        # Should be valid JSON now
        data = json.loads(repaired)
        assert "searches" in data
        assert len(data["searches"]) == 1
        assert data["searches"][0]["query"] == "query 1"
