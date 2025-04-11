"""
Unit tests for the manager module.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from reagents.manager import ResearchManager
from reagents.agents.planner_agent import WebSearchItem, WebSearchPlan


class TestResearchManager:
    """Tests for the ResearchManager class."""

    def test_init(self, mock_console):
        """Test that the constructor initializes the manager correctly."""
        # Create a manager
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class:

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Create the manager
            manager = ResearchManager()

            # Check that the manager was initialized correctly
            assert manager.console is not None
            assert manager.printer == mock_printer
            assert manager.persistence == mock_persistence
            assert manager.session_id is None

    def test_init_with_session_id(self, mock_console):
        """Test that the constructor initializes the manager with a session ID."""
        # Create a manager with a session ID
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class:

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Create the manager
            manager = ResearchManager(session_id="test_session")

            # Check that the manager was initialized correctly
            assert manager.console is not None
            assert manager.printer == mock_printer
            assert manager.persistence == mock_persistence
            assert manager.session_id == "test_session"

    @pytest.mark.asyncio
    async def test_run_new_session(self, mock_console, mock_runner):
        """Test running a new research session."""
        # Create a manager
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class, \
             patch('reagents.manager.gen_trace_id', return_value="test_trace_id"), \
             patch('reagents.manager.trace'):

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Mock the manager's methods
            with patch.object(ResearchManager, '_plan_searches', new_callable=AsyncMock) as mock_plan, \
                 patch.object(ResearchManager, '_perform_searches', new_callable=AsyncMock) as mock_search, \
                 patch.object(ResearchManager, '_write_report', new_callable=AsyncMock) as mock_write:

                # Configure the mocks
                mock_plan.return_value = WebSearchPlan(searches=[WebSearchItem(query="test", reason="test")])
                mock_search.return_value = ["Test result"]
                mock_write.return_value = MagicMock()

                # Create the manager
                manager = ResearchManager()

                # Run the manager
                await manager.run("Test query")

                # Check that the methods were called
                mock_plan.assert_called_once_with("Test query")
                mock_search.assert_called_once()
                mock_write.assert_called_once_with("Test query", ["Test result"])

                # Check that the persistence methods were called
                mock_persistence.save_search_plan.assert_called_once()
                mock_persistence.update_search_plan.assert_called_once()
                mock_persistence.save_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_resume_session(self, mock_console, mock_runner):
        """Test resuming an existing research session."""
        # Create a manager
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class, \
             patch('reagents.manager.gen_trace_id', return_value="test_trace_id"), \
             patch('reagents.manager.trace'):

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Configure the session data
            session_data = {
                "query": "Test query",
                "status": "planned",
                "search_plan": {"searches": [{"query": "test", "reason": "test"}]},
                "timestamp": "2023-01-01T00:00:00"
            }
            mock_persistence.get_session_data.return_value = session_data

            # Mock the manager's methods
            with patch.object(ResearchManager, '_plan_searches', new_callable=AsyncMock) as mock_plan, \
                 patch.object(ResearchManager, '_perform_searches', new_callable=AsyncMock) as mock_search, \
                 patch.object(ResearchManager, '_write_report', new_callable=AsyncMock) as mock_write:

                # Configure the mocks
                mock_search.return_value = ["Test result"]
                mock_write.return_value = MagicMock()

                # Create the manager with a session ID
                manager = ResearchManager(session_id="test_session")

                # Run the manager
                await manager.run("Test query")

                # Check that the methods were called appropriately
                mock_plan.assert_not_called()  # Should not be called for a resumed session
                mock_search.assert_called_once()
                mock_write.assert_called_once_with("Test query", ["Test result"])

                # Check that the persistence methods were called
                mock_persistence.get_session_data.assert_called_once_with("test_session")
                mock_persistence.update_search_plan.assert_called_once()
                mock_persistence.save_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_plan_searches(self, mock_console, mock_runner):
        """Test the _plan_searches method."""
        # Create a manager
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class, \
             patch('reagents.manager.planner_agent') as mock_planner_agent:

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Create a mock response for the planner agent
            mock_response = MagicMock()
            mock_response.final_output = '{"searches": [{"query": "test query", "reason": "test reason"}]}'
            mock_runner.run.return_value = mock_response

            # Create the manager
            manager = ResearchManager()

            # Call the method
            plan = await manager._plan_searches("Test query")

            # Check that the runner was called
            mock_runner.run.assert_called_once_with(mock_planner_agent, "Query: Test query")

            # Check the result
            assert isinstance(plan, WebSearchPlan)
            assert len(plan.searches) == 1
            assert plan.searches[0].query == "test query"
            assert plan.searches[0].reason == "test reason"

    @pytest.mark.asyncio
    async def test_perform_searches(self, mock_console, mock_runner):
        """Test the _perform_searches method."""
        # Create a manager
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class, \
             patch.object(ResearchManager, '_search', new_callable=AsyncMock) as mock_search:

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Configure the search mock to return different results for different queries
            async def search_side_effect(item):
                if item.query == "query 1":
                    return "Result 1"
                elif item.query == "query 2":
                    return "Result 2"
                else:
                    return None

            mock_search.side_effect = search_side_effect

            # Create a search plan
            plan = WebSearchPlan(
                searches=[
                    WebSearchItem(query="query 1", reason="reason 1"),
                    WebSearchItem(query="query 2", reason="reason 2"),
                    WebSearchItem(query="query 3", reason="reason 3")  # This one will return None
                ]
            )

            # Create the manager
            manager = ResearchManager()

            # Call the method
            results = await manager._perform_searches(plan)

            # Check that the search method was called for each query
            assert mock_search.call_count == 3

            # Check the results
            assert len(results) == 2  # Only 2 results because the third search returned None
            assert "Result 1" in results
            assert "Result 2" in results

    @pytest.mark.asyncio
    async def test_search(self, mock_console, mock_runner):
        """Test the _search method."""
        # Create a manager
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class, \
             patch('reagents.manager.search_agent') as mock_search_agent:

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Create a mock response for the search agent
            mock_response = MagicMock()
            mock_response.final_output = "Test search result"
            mock_runner.run.return_value = mock_response

            # Create the manager
            manager = ResearchManager()

            # Call the method
            result = await manager._search(WebSearchItem(query="test query", reason="test reason"))

            # Check that the runner was called
            mock_runner.run.assert_called_once_with(
                mock_search_agent,
                "Search term: test query\nReason for searching: test reason"
            )

            # Check the result
            assert result == "Test search result"

    @pytest.mark.asyncio
    async def test_search_with_long_query(self, mock_console, mock_runner):
        """Test the _search method with a long query that needs truncation."""
        # Create a manager
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class, \
             patch('reagents.manager.search_agent') as mock_search_agent:

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Create a mock response for the search agent
            mock_response = MagicMock()
            mock_response.final_output = "Test search result"
            mock_runner.run.return_value = mock_response

            # Create the manager
            manager = ResearchManager()

            # Create a very long query
            long_query = "a" * 300

            # Call the method
            result = await manager._search(WebSearchItem(query=long_query, reason="test reason"))

            # Check that the runner was called with a truncated query
            call_args = mock_runner.run.call_args[0]
            assert len(call_args[1]) < 300 + len("Search term: \nReason for searching: test reason")

            # Check the result
            assert result == "Test search result"

    @pytest.mark.asyncio
    async def test_search_with_timeout(self, mock_console):
        """Test the _search method with a timeout."""
        # Create a manager
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class, \
             patch('reagents.manager.search_agent') as mock_search_agent, \
             patch('reagents.manager.Runner.run', new_callable=AsyncMock) as mock_run:

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Make the run method take a long time
            async def slow_run(*args, **kwargs):
                await asyncio.sleep(0.1)  # Just a small delay for testing
                raise asyncio.TimeoutError("Test timeout")

            mock_run.side_effect = slow_run

            # Create the manager
            manager = ResearchManager()

            # Call the method
            result = await manager._search(WebSearchItem(query="test query", reason="test reason"))

            # Check that the result indicates a timeout
            assert "timed out" in result.lower()

    @pytest.mark.asyncio
    async def test_write_report(self, mock_console, mock_runner):
        """Test the _write_report method."""
        # Create a manager
        with patch('reagents.manager.Printer') as mock_printer_class, \
             patch('reagents.manager.ResearchPersistence') as mock_persistence_class, \
             patch('reagents.manager.writer_agent') as mock_writer_agent:

            # Configure the mocks
            mock_printer = MagicMock()
            mock_printer_class.return_value = mock_printer

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Create a mock response for the writer agent
            mock_stream_result = MagicMock()
            mock_stream_result.final_output = '{"short_summary": "Test summary", "markdown_report": "Test report", "follow_up_questions": ["Q1?", "Q2?"]}'

            # Configure the stream_events method to be an async generator
            async def mock_stream_events():
                yield {"type": "content", "content": "Test"}

            mock_stream_result.stream_events = mock_stream_events
            mock_runner.run_streamed.return_value = mock_stream_result

            # Create the manager
            manager = ResearchManager()

            # Call the method
            report = await manager._write_report("Test query", ["Test result 1", "Test result 2"])

            # Check that the runner was called
            mock_runner.run_streamed.assert_called_once()

            # Check the result
            assert report.short_summary == "Test summary"
            assert report.markdown_report == "Test report"
            assert report.follow_up_questions == ["Q1?", "Q2?"]
