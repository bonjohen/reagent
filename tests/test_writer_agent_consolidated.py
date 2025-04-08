"""
Tests for the consolidated writer agent.
"""

import json
import pytest
from research_agent.agents.writer_agent_consolidated import ReportData

def test_report_data_from_valid_json():
    """Test that ReportData.from_response correctly parses valid JSON."""
    valid_json = """
    {
        "short_summary": "This is a test summary",
        "markdown_report": "# Test Report\n\nThis is a test report.",
        "follow_up_questions": ["Question 1", "Question 2"]
    }
    """

    report_data = ReportData.from_response(valid_json, model="test-model")

    assert report_data.short_summary == "This is a test summary"
    assert report_data.markdown_report == "# Test Report\n\nThis is a test report."
    assert report_data.follow_up_questions == ["Question 1", "Question 2"]
    assert report_data.model == "test-model"

def test_report_data_from_json_with_code_blocks():
    """Test that ReportData.from_response correctly parses JSON wrapped in code blocks."""
    json_with_code_blocks = """
    Some text before the JSON.

    ```json
    {
        "short_summary": "This is a test summary",
        "markdown_report": "# Test Report\n\nThis is a test report.",
        "follow_up_questions": ["Question 1", "Question 2"]
    }
    ```

    Some text after the JSON.
    """

    report_data = ReportData.from_response(json_with_code_blocks, model="test-model")

    assert report_data.short_summary == "This is a test summary"
    assert report_data.markdown_report == "# Test Report\n\nThis is a test report."
    assert report_data.follow_up_questions == ["Question 1", "Question 2"]
    assert report_data.model == "test-model"

def test_json_repair_missing_follow_up_questions():
    """Test that _attempt_json_repair adds default follow-up questions if missing."""
    json_missing_follow_up = """
    {
        "short_summary": "This is a test summary",
        "markdown_report": "# Test Report\n\nThis is a test report."
    }
    """

    # Access the private method through the class
    repaired_json = ReportData._attempt_json_repair(json_missing_follow_up)
    data = json.loads(repaired_json)

    assert "follow_up_questions" in data
    assert len(data["follow_up_questions"]) == 5
    assert "What are the most recent developments in this field?" in data["follow_up_questions"]

def test_json_repair_newlines_in_markdown():
    """Test that _attempt_json_repair correctly handles newlines in markdown content."""
    json_with_newlines = """
    {
        "short_summary": "This is a test summary",
        "markdown_report": "# Test Report

This is a test report with
multiple lines.

## Section 1
Content for section 1.

## Section 2
Content for section 2.",
        "follow_up_questions": ["Question 1", "Question 2"]
    }
    """

    # Access the private method through the class
    repaired_json = ReportData._attempt_json_repair(json_with_newlines)

    # This should not raise an exception
    data = json.loads(repaired_json)

    assert data["short_summary"] == "This is a test summary"
    assert "# Test Report" in data["markdown_report"]
    assert "## Section 1" in data["markdown_report"]
    assert "## Section 2" in data["markdown_report"]
    assert data["follow_up_questions"] == ["Question 1", "Question 2"]

def test_fallback_report_on_invalid_json():
    """Test that ReportData.from_response creates a fallback report for invalid JSON."""
    # This is not even JSON, just some random text
    invalid_json = "This is not JSON at all, just some random text."

    report_data = ReportData.from_response(invalid_json, model="test-model")

    assert "Error parsing report" in report_data.short_summary
    assert "# Error in Report Generation" in report_data.markdown_report
    assert len(report_data.follow_up_questions) == 2
    assert "What went wrong with the report generation?" in report_data.follow_up_questions
