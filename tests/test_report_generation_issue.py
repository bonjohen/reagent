"""
Test to demonstrate the issue with report generation.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock, AsyncMock

from reagents.manager import ResearchManager
from reagents.agents.writer_agent import ReportData


@pytest.mark.asyncio
async def test_report_generation_failure():
    """Test that the report generation properly handles failures and creates appropriate error messages."""
    # Mock search results similar to what we see in the actual JSON file
    search_results = [
        "Search results for 'current research on efficient graphene production':\n\nTitle: Latest Breakthroughs...",
        "Search results for 'chemical vapor deposition graphene production':\n\nTitle: CVD Graphene...",
        "Search results for 'methods for producing graphene':\n\nTitle: Graphene production techniques...",
        "Search results for 'cost analysis of graphene production':\n\nTitle: Analysis of the materials...",
        "Search results for 'environmental impact of graphene production':\n\nTitle: The Environmental Impact...",
        "Search results for 'top graphene producers worldwide':\n\nTitle: 11 Graphene Manufacturers...",
        "Search results for 'industrial graphene manufacturing processes':\n\nTitle: Mass-Producing Graphene...",
        "Search results for 'graphene oxide reduction methods':\n\nTitle: Strategies for reduction..."
    ]

    # Create a mock for the Runner.run_streamed method that returns None for final_output
    # This simulates the scenario where the agent fails to generate a proper response
    mock_result = MagicMock()
    mock_result.final_output = None

    # Create a mock for the printer
    mock_printer = MagicMock()
    mock_printer.update_item = MagicMock()

    # Create a mock for the persistence
    mock_persistence = MagicMock()

    # Create a research manager with mocked dependencies
    manager = ResearchManager()
    manager.printer = mock_printer
    manager.persistence = mock_persistence

    # Mock the Runner.run_streamed method to return our mock_result
    with patch('agents.Runner.run_streamed', return_value=mock_result):
        # Call the _write_report method
        query = "Graphene production"
        report_data = await manager._write_report(query, search_results)

        # Check that the report data contains the error message
        assert "ERROR: Failed to generate report" in report_data.short_summary
        assert "Graphene production" in report_data.short_summary

        # Check that the markdown report contains appropriate error information
        assert "Unable to generate a complete report due to an error" in report_data.markdown_report
        assert "search results were retrieved successfully" in report_data.markdown_report

        # Verify that follow-up questions are provided as a fallback
        assert len(report_data.follow_up_questions) > 0


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_report_generation_failure())
