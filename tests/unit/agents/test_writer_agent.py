"""
Unit tests for the writer_agent module.
"""
import pytest
import json
from unittest.mock import patch

from reagents.agents.writer_agent import ReportData


class TestWriterAgent:
    """Tests for the writer_agent module."""

    def test_report_data_model(self):
        """Test the ReportData model."""
        # Create a ReportData instance
        report = ReportData(
            short_summary="Test summary",
            markdown_report="# Test Report\n\nThis is a test report.",
            follow_up_questions=["Question 1?", "Question 2?"]
        )
        
        # Check the fields
        assert report.short_summary == "Test summary"
        assert report.markdown_report == "# Test Report\n\nThis is a test report."
        assert report.follow_up_questions == ["Question 1?", "Question 2?"]

    def test_from_response_json_format(self):
        """Test parsing a JSON response."""
        # Create a JSON response
        response_data = {
            "short_summary": "Test summary",
            "markdown_report": "# Test Report\n\nThis is a test report.",
            "follow_up_questions": ["Question 1?", "Question 2?"]
        }
        response = json.dumps(response_data)
        
        # Parse the response
        report = ReportData.from_response(response)
        
        # Check the parsed data
        assert report.short_summary == "Test summary"
        assert report.markdown_report == "# Test Report\n\nThis is a test report."
        assert report.follow_up_questions == ["Question 1?", "Question 2?"]

    def test_from_response_markdown_json_format(self):
        """Test parsing a JSON response wrapped in markdown code blocks."""
        # Create a JSON response wrapped in markdown
        response_data = {
            "short_summary": "Test summary",
            "markdown_report": "# Test Report\n\nThis is a test report.",
            "follow_up_questions": ["Question 1?", "Question 2?"]
        }
        response = f"```json\n{json.dumps(response_data)}\n```"
        
        # Parse the response
        report = ReportData.from_response(response)
        
        # Check the parsed data
        assert report.short_summary == "Test summary"
        assert report.markdown_report == "# Test Report\n\nThis is a test report."
        assert report.follow_up_questions == ["Question 1?", "Question 2?"]

    def test_from_response_code_block_format(self):
        """Test parsing a JSON response wrapped in generic code blocks."""
        # Create a JSON response wrapped in generic code blocks
        response_data = {
            "short_summary": "Test summary",
            "markdown_report": "# Test Report\n\nThis is a test report.",
            "follow_up_questions": ["Question 1?", "Question 2?"]
        }
        response = f"```\n{json.dumps(response_data)}\n```"
        
        # Parse the response
        report = ReportData.from_response(response)
        
        # Check the parsed data
        assert report.short_summary == "Test summary"
        assert report.markdown_report == "# Test Report\n\nThis is a test report."
        assert report.follow_up_questions == ["Question 1?", "Question 2?"]

    def test_from_response_invalid_json(self):
        """Test parsing an invalid JSON response."""
        # Create an invalid JSON response
        response = "This is not valid JSON"
        
        # Parse the response - should create a fallback report
        report = ReportData.from_response(response)
        
        # Check that a fallback report was created
        assert "Error parsing report" in report.short_summary
        assert "Error in Report Generation" in report.markdown_report
        assert len(report.follow_up_questions) > 0

    def test_from_response_missing_fields(self):
        """Test parsing a JSON response with missing fields."""
        # Create a JSON response with missing fields
        response_data = {
            "short_summary": "Test summary"
            # Missing markdown_report and follow_up_questions
        }
        response = json.dumps(response_data)
        
        # Parse the response - should create a fallback report
        report = ReportData.from_response(response)
        
        # Check that a fallback report was created
        assert "Error parsing report" in report.short_summary
        assert "Error in Report Generation" in report.markdown_report
        assert len(report.follow_up_questions) > 0

    def test_json_repair(self):
        """Test the JSON repair functionality."""
        # Test various common JSON errors
        
        # Single quotes instead of double quotes
        invalid_json = "{'short_summary': 'Test summary', 'markdown_report': 'Test report', 'follow_up_questions': ['Q1?', 'Q2?']}"
        repaired = ReportData._attempt_json_repair(invalid_json)
        # Should be valid JSON now
        data = json.loads(repaired)
        assert data["short_summary"] == "Test summary"
        
        # Unquoted keys
        invalid_json = "{short_summary: \"Test summary\", markdown_report: \"Test report\", follow_up_questions: [\"Q1?\", \"Q2?\"]}"
        repaired = ReportData._attempt_json_repair(invalid_json)
        # Should be valid JSON now
        data = json.loads(repaired)
        assert data["short_summary"] == "Test summary"
        
        # Trailing commas
        invalid_json = "{\"short_summary\": \"Test summary\", \"markdown_report\": \"Test report\", \"follow_up_questions\": [\"Q1?\", \"Q2?\", ]}"
        repaired = ReportData._attempt_json_repair(invalid_json)
        # Should be valid JSON now
        data = json.loads(repaired)
        assert data["short_summary"] == "Test summary"
