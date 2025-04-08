"""
Tests for the writer agent.
"""

import json
import pytest
from reagents.agents.writer_agent import ReportData

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
    ```json
    {
        "short_summary": "This is a test summary",
        "markdown_report": "# Test Report\n\nThis is a test report.",
        "follow_up_questions": ["Question 1", "Question 2"]
    }
    ```
    """

    report_data = ReportData.from_response(json_with_code_blocks, model="test-model")

    assert report_data.short_summary == "This is a test summary"
    assert report_data.markdown_report == "# Test Report\n\nThis is a test report."
    assert report_data.follow_up_questions == ["Question 1", "Question 2"]
    assert report_data.model == "test-model"

def test_json_repair_missing_follow_up_questions():
    """Test that _attempt_json_repair adds default follow_up_questions if missing."""
    json_missing_questions = """
    {
        "short_summary": "This is a test summary",
        "markdown_report": "# Test Report\n\nThis is a test report."
    }
    """

    report_data = ReportData.from_response(json_missing_questions, model="test-model")

    assert report_data.short_summary == "This is a test summary"
    assert report_data.markdown_report == "# Test Report\n\nThis is a test report."
    assert len(report_data.follow_up_questions) > 0
    assert report_data.model == "test-model"

def test_json_repair_newlines_in_markdown():
    """Test that _attempt_json_repair handles newlines in markdown_report."""
    json_with_newlines = """
    {
        "short_summary": "This is a test summary",
        "markdown_report": "# Test Report\n\nThis is a test report with newlines.\nAnd another line.\n\nAnd a paragraph.",
        "follow_up_questions": ["Question 1", "Question 2"]
    }
    """

    report_data = ReportData.from_response(json_with_newlines, model="test-model")

    assert report_data.short_summary == "This is a test summary"
    assert "# Test Report" in report_data.markdown_report
    assert "This is a test report with newlines." in report_data.markdown_report
    assert "And another line." in report_data.markdown_report
    assert "And a paragraph." in report_data.markdown_report
    assert report_data.follow_up_questions == ["Question 1", "Question 2"]
    assert report_data.model == "test-model"

def test_fallback_report_on_invalid_json():
    """Test that from_response creates a fallback report on invalid JSON."""
    invalid_json = """
    This is not valid JSON at all.
    """

    report_data = ReportData.from_response(invalid_json, model="test-model")

    assert "Error parsing report" in report_data.short_summary
    assert "Error in Report Generation" in report_data.markdown_report
    assert "This is not valid JSON at all." in report_data.markdown_report
    assert len(report_data.follow_up_questions) > 0
    assert "report generation" in report_data.follow_up_questions[0].lower()
