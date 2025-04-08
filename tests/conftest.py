"""
Common test fixtures and configuration for all tests.
"""
import os
import pytest
import tempfile
import json
from unittest.mock import MagicMock, patch

from reagents.agents.planner_agent import WebSearchItem, WebSearchPlan
from reagents.agents.writer_agent import ReportData


@pytest.fixture
def mock_console():
    """Mock console for testing printer functionality."""
    console = MagicMock()
    console.print = MagicMock()
    return console


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_search_plan():
    """Create a sample search plan for testing."""
    return WebSearchPlan(
        searches=[
            WebSearchItem(
                query="test query 1",
                reason="test reason 1"
            ),
            WebSearchItem(
                query="test query 2",
                reason="test reason 2"
            )
        ]
    )


@pytest.fixture
def sample_search_results():
    """Create sample search results for testing."""
    return [
        "Result 1: This is a test result for the first query.",
        "Result 2: This is a test result for the second query."
    ]


@pytest.fixture
def sample_report_data():
    """Create sample report data for testing."""
    return ReportData(
        short_summary="This is a test summary",
        markdown_report="# Test Report\n\nThis is a test report.",
        follow_up_questions=["Question 1?", "Question 2?"]
    )


@pytest.fixture
def mock_runner():
    """Mock the Runner class from the agents package."""
    with patch('agents.Runner') as mock:
        # Configure the mock to return appropriate values
        run_result = MagicMock()
        run_result.final_output = "Test output"
        mock.run.return_value = run_result
        
        # For streaming results
        stream_result = MagicMock()
        stream_result.final_output = "Test streaming output"
        stream_result.stream_events = MagicMock()
        mock.run_streamed.return_value = stream_result
        
        yield mock
