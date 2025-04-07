"""
Unit tests for the main module.
"""
import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock

import main


class TestMain:
    """Tests for the main module."""

    def test_is_valid_api_key(self):
        """Test the is_valid_api_key function."""
        # Valid API key
        # Use a valid pattern but with a test prefix to avoid using real API key format
        assert main.is_valid_api_key("sk-test1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN")

        # Invalid API keys
        assert not main.is_valid_api_key("not-a-key")  # Doesn't start with sk-
        assert not main.is_valid_api_key("sk-tooshort")  # Too short
        assert not main.is_valid_api_key("sk-" + "a" * 50 + "!")  # Invalid character

    def test_check_api_key(self):
        """Test the check_api_key function."""
        with patch('builtins.print'):
            # Valid API key
            # Use a test prefix to avoid using real API key format
            assert main.check_api_key("sk-test1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN", allow_prompt=False)

            # Invalid API key in non-interactive mode
            assert not main.check_api_key("invalid-key", allow_prompt=False)

    def test_list_sessions(self):
        """Test the list_sessions function."""
        with patch('main.ResearchPersistence') as mock_persistence_class, \
             patch('builtins.print') as mock_print:

            # Configure the mock
            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Configure the list_sessions method to return some sessions
            mock_persistence.list_sessions.return_value = [
                {
                    "session_id": "session1",
                    "query": "Query 1",
                    "status": "completed",
                    "timestamp": "2023-01-01T00:00:00"
                },
                {
                    "session_id": "session2",
                    "query": "Query 2",
                    "status": "planned",
                    "timestamp": "2023-01-02T00:00:00"
                }
            ]

            # Call the function
            main.list_sessions()

            # Check that the persistence method was called
            mock_persistence.list_sessions.assert_called_once()

            # Check that print was called with the expected output
            assert mock_print.call_count > 0
            # We can't easily check the exact output, but we can check that it was called

    @pytest.mark.asyncio
    async def test_main_list_option(self):
        """Test the main function with the --list option."""
        with patch('main.argparse.ArgumentParser.parse_args') as mock_parse_args, \
             patch('main.list_sessions') as mock_list_sessions, \
             patch('main.ResearchManager') as mock_manager_class:

            # Configure the mock to return args with list=True
            mock_args = MagicMock()
            mock_args.list = True
            mock_args.resume = None
            mock_parse_args.return_value = mock_args

            # Call the function
            await main.main()

            # Check that list_sessions was called
            mock_list_sessions.assert_called_once()

            # Check that ResearchManager was not called
            mock_manager_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_main_resume_option(self):
        """Test the main function with the --resume option."""
        with patch('main.argparse.ArgumentParser.parse_args') as mock_parse_args, \
             patch('main.ResearchManager') as mock_manager_class, \
             patch('main.ResearchPersistence') as mock_persistence_class, \
             patch('builtins.print') as mock_print:

            # Configure the mocks
            mock_args = MagicMock()
            mock_args.list = False
            mock_args.resume = "test_session"
            mock_parse_args.return_value = mock_args

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager

            # Configure the get_session_data method to return a session
            mock_persistence.get_session_data.return_value = {
                "query": "Test query",
                "status": "planned",
                "search_plan": {"searches": [{"query": "test", "reason": "test"}]},
                "timestamp": "2023-01-01T00:00:00"
            }

            # Call the function
            await main.main()

            # Check that the persistence method was called
            mock_persistence.get_session_data.assert_called_once_with("test_session")

            # Check that the manager was created and run
            mock_manager_class.assert_called_once_with(session_id="test_session")
            mock_manager.run.assert_called_once_with("Test query")

    @pytest.mark.asyncio
    async def test_main_resume_nonexistent_session(self):
        """Test the main function with a nonexistent session ID."""
        with patch('main.argparse.ArgumentParser.parse_args') as mock_parse_args, \
             patch('main.ResearchManager') as mock_manager_class, \
             patch('main.ResearchPersistence') as mock_persistence_class, \
             patch('builtins.print') as mock_print:

            # Configure the mocks
            mock_args = MagicMock()
            mock_args.list = False
            mock_args.resume = "nonexistent_session"
            mock_parse_args.return_value = mock_args

            mock_persistence = MagicMock()
            mock_persistence_class.return_value = mock_persistence

            # Configure the get_session_data method to return None
            mock_persistence.get_session_data.return_value = None

            # Call the function
            await main.main()

            # Check that the persistence method was called
            mock_persistence.get_session_data.assert_called_once_with("nonexistent_session")

            # Check that the manager was not created
            mock_manager_class.assert_not_called()

            # Check that an error message was printed
            mock_print.assert_any_call(f"Error: Session nonexistent_session not found.")

    @pytest.mark.asyncio
    async def test_main_new_query(self):
        """Test the main function with a new query."""
        with patch('main.argparse.ArgumentParser.parse_args') as mock_parse_args, \
             patch('main.ResearchManager') as mock_manager_class, \
             patch('builtins.input', return_value="Test query"), \
             patch('builtins.print') as mock_print:

            # Configure the mocks
            mock_args = MagicMock()
            mock_args.list = False
            mock_args.resume = None
            mock_parse_args.return_value = mock_args

            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager

            # Call the function
            await main.main()

            # Check that the manager was created and run
            mock_manager_class.assert_called_once_with(session_id=None)
            mock_manager.run.assert_called_once_with("Test query")

    @pytest.mark.asyncio
    async def test_main_empty_query(self):
        """Test the main function with an empty query."""
        with patch('main.argparse.ArgumentParser.parse_args') as mock_parse_args, \
             patch('main.ResearchManager') as mock_manager_class, \
             patch('builtins.input', return_value=""), \
             patch('builtins.print') as mock_print:

            # Configure the mocks
            mock_args = MagicMock()
            mock_args.list = False
            mock_args.resume = None
            mock_parse_args.return_value = mock_args

            # Call the function
            await main.main()

            # Check that the manager was not created
            mock_manager_class.assert_not_called()

            # Check that an error message was printed
            mock_print.assert_any_call("Error: Please provide a non-empty research query.")
