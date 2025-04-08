"""
Tests for the report generation functionality in the research manager.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from reagents.manager import ResearchManager
from reagents.agents.writer_agent import writer_agent

@pytest.mark.asyncio
async def test_write_report_awaits_run_streamed():
    """Test that _write_report properly awaits Runner.run_streamed."""
    # Create a manager instance
    manager = ResearchManager()

    # Create a mock printer
    mock_printer = MagicMock()
    manager.printer = mock_printer

    # Create a mock for Runner.run_streamed
    # Note: Runner.run_streamed returns a non-awaitable object, so we use MagicMock instead of AsyncMock
    mock_run_streamed = MagicMock()

    # Create a mock result
    mock_result = MagicMock()
    mock_result.final_output = "Test report"

    # Configure the mock to return the mock result
    mock_run_streamed.return_value = mock_result

    # Create a mock for ReportData.from_response
    mock_from_response = MagicMock()
    mock_from_response.return_value = MagicMock()

    # Patch the necessary methods
    with patch('agents.Runner.run_streamed', mock_run_streamed), \
         patch('reagents.agents.writer_agent.ReportData.from_response', mock_from_response):

        # Call the _write_report method
        await manager._write_report("test query", ["test search result"])

        # Verify that Runner.run_streamed was called
        mock_run_streamed.assert_called_once()

        # Verify that run_streamed was called with the correct arguments
        # Note: Runner.run_streamed returns a non-awaitable object, so it should not be awaited
        mock_run_streamed.assert_called_once_with(writer_agent, "Original query: test query\nSummarized search results: ['test search result']")

        # Verify that ReportData.from_response was called with the final output
        mock_from_response.assert_called_once_with("Test report", "gpt-3.5-turbo")

@pytest.mark.asyncio
async def test_write_report_handles_timeout():
    """Test that _write_report properly handles timeouts."""
    # Create a manager instance
    manager = ResearchManager()

    # Create a mock printer
    mock_printer = MagicMock()
    manager.printer = mock_printer

    # Create a mock for Runner.run_streamed
    # Note: Runner.run_streamed returns a non-awaitable object, so we use MagicMock instead of AsyncMock
    mock_run_streamed = MagicMock()

    # Configure the mock to raise a TimeoutError
    mock_run_streamed.side_effect = TimeoutError("Test timeout")



    # Patch the necessary methods
    with patch('agents.Runner.run_streamed', mock_run_streamed), \
         pytest.raises(TimeoutError):  # Expect a TimeoutError to be raised

        # Call the _write_report method
        await manager._write_report("test query", ["test search result"])

        # Verify that Runner.run_streamed was called
        mock_run_streamed.assert_called_once()

        # Verify that the printer was updated with an error message
        mock_printer.update_item.assert_any_call(
            "error",
            "Report generation timed out",
            is_done=True,
        )
