import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os

from reagents.agents.writer_agent import WriterAgent, ReportData


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
    
    # Create a mock for the writer_agent.run_streamed method that returns None for final_output
    # This simulates the scenario where the agent fails to generate a proper response
    mock_result = MagicMock()
    mock_result.final_output = None
    
    # Create a writer agent instance
    writer_agent = WriterAgent()
    
    # Mock the run_streamed method to return our mock_result
    with patch('reagents.agents.writer_agent.writer_agent.run_streamed', 
               return_value=mock_result) as mock_run_streamed:
        # Call the generate_report method
        query = "Graphene production"
        report_data = await writer_agent.generate_report(query, search_results)
        
        # Verify that run_streamed was called
        mock_run_streamed.assert_called_once()
        
        # Check that the report data contains the error message
        assert "ERROR: Failed to generate report" in report_data.short_summary
        assert "Graphene production" in report_data.short_summary
        
        # Check that the markdown report contains appropriate error information
        assert "Unable to generate a report due to an error" in report_data.markdown_report
        assert "search results were found" in report_data.markdown_report
        
        # Verify that follow-up questions are provided as a fallback
        assert len(report_data.follow_up_questions) > 0


@pytest.mark.asyncio
async def test_report_generation_with_invalid_search_results():
    """Test that the report generation handles invalid search results properly."""
    # Test with empty search results
    writer_agent = WriterAgent()
    query = "Graphene production"
    
    # Test with empty list
    report_data = await writer_agent.generate_report(query, [])
    assert "ERROR: Failed to generate report" in report_data.short_summary
    assert "no valid search results" in report_data.markdown_report.lower()
    
    # Test with None
    report_data = await writer_agent.generate_report(query, None)
    assert "ERROR: Failed to generate report" in report_data.short_summary
    assert "invalid search results" in report_data.markdown_report.lower()
    
    # Test with non-string items in the list
    report_data = await writer_agent.generate_report(query, [None, 123, {"key": "value"}])
    assert "ERROR: Failed to generate report" in report_data.short_summary
    assert "invalid" in report_data.markdown_report.lower()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_report_generation_failure())
    asyncio.run(test_report_generation_with_invalid_search_results())
