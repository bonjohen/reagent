"""
Unit tests for the persistence module.
"""
import os
import json
import pytest
from unittest.mock import patch, mock_open

from reagents.persistence import ResearchPersistence


class TestResearchPersistence:
    """Tests for the ResearchPersistence class."""

    def test_init_creates_directory(self, temp_data_dir):
        """Test that the constructor creates the data directory if it doesn't exist."""
        test_dir = os.path.join(temp_data_dir, "test_data")
        assert not os.path.exists(test_dir)

        persistence = ResearchPersistence(data_dir=test_dir)
        assert os.path.exists(test_dir)

    def test_generate_session_id(self):
        """Test that _generate_session_id creates a valid session ID."""
        persistence = ResearchPersistence()
        session_id = persistence._generate_session_id("Test query with spaces and special chars!?")

        # Check format: timestamp_simplified_query
        assert "_" in session_id
        parts = session_id.split("_", 1)
        assert len(parts) == 2

        # Check timestamp part is numeric
        assert parts[0].isdigit()

        # Check query part has been simplified
        assert "Test_query_with_spaces" in parts[1]
        assert "!?" not in parts[1]

    def test_save_search_plan(self, temp_data_dir):
        """Test saving a search plan."""
        persistence = ResearchPersistence(data_dir=temp_data_dir)

        query = "Test query"
        search_plan = {"searches": [{"query": "test", "reason": "testing"}]}
        search_questions = {"questions": ["What is test?", "How does test work?"], "count": 2}

        session_id = persistence.save_search_plan(query, search_plan, search_questions)

        # Check that the file was created
        file_path = os.path.join(temp_data_dir, f"{session_id}.json")
        assert os.path.exists(file_path)

        # Check file contents
        with open(file_path, "r") as f:
            data = json.load(f)
            assert data["query"] == query
            assert data["search_plan"] == search_plan
            assert data["search_questions"] == search_questions
            assert data["status"] == "planned"
            assert "timestamp" in data

    def test_update_search_plan(self, temp_data_dir):
        """Test updating a search plan."""
        persistence = ResearchPersistence(data_dir=temp_data_dir)

        # First create a session
        query = "Test query"
        search_plan = {"searches": [{"query": "test", "reason": "testing"}]}
        session_id = persistence.save_search_plan(query, search_plan)

        # Now update the search plan
        updated_search_plan = {"searches": [{"query": "test", "reason": "testing", "result": "Test result"}]}
        search_questions = {"questions": ["What is test?", "How does test work?"], "count": 2}
        persistence.update_search_plan(session_id, updated_search_plan, search_questions)

        # Check file contents
        file_path = os.path.join(temp_data_dir, f"{session_id}.json")
        with open(file_path, "r") as f:
            data = json.load(f)
            assert data["search_plan"] == updated_search_plan
            assert data["search_questions"] == search_questions
            assert data["status"] == "searched"

    def test_save_report(self, temp_data_dir):
        """Test saving a report."""
        persistence = ResearchPersistence(data_dir=temp_data_dir)

        # First create a session with search results
        query = "Test query"
        search_plan = {"searches": [{"query": "test", "reason": "testing"}]}
        session_id = persistence.save_search_plan(query, search_plan)

        # Update the search plan with results
        updated_search_plan = {"searches": [{"query": "test", "reason": "testing", "result": "Test result"}]}
        persistence.update_search_plan(session_id, updated_search_plan)

        # Now save a report
        report = {
            "short_summary": "Test summary",
            "markdown_report": "# Test Report",
            "follow_up_questions": ["Q1?", "Q2?"]
        }
        persistence.save_report(session_id, report)

        # Check file contents
        file_path = os.path.join(temp_data_dir, f"{session_id}.json")
        with open(file_path, "r") as f:
            data = json.load(f)
            assert data["status"] == "completed"

    def test_get_session_data(self, temp_data_dir):
        """Test retrieving session data."""
        persistence = ResearchPersistence(data_dir=temp_data_dir)

        # Create a session
        query = "Test query"
        search_plan = {"searches": [{"query": "test", "reason": "testing"}]}
        session_id = persistence.save_search_plan(query, search_plan)

        # Retrieve the session data
        data = persistence.get_session_data(session_id)

        assert data["query"] == query
        assert data["search_plan"] == search_plan
        assert data["status"] == "planned"

    def test_get_session_data_nonexistent(self, temp_data_dir):
        """Test retrieving data for a nonexistent session."""
        persistence = ResearchPersistence(data_dir=temp_data_dir)

        data = persistence.get_session_data("nonexistent_session")
        assert data is None

    def test_list_sessions(self, temp_data_dir):
        """Test listing all sessions."""
        persistence = ResearchPersistence(data_dir=temp_data_dir)

        # Create a few sessions
        queries = ["Query 1", "Query 2", "Query 3"]
        session_ids = []

        for query in queries:
            search_plan = {"searches": [{"query": query, "reason": "testing"}]}
            session_id = persistence.save_search_plan(query, search_plan)
            session_ids.append(session_id)

        # List sessions
        sessions = persistence.list_sessions()

        assert len(sessions) == len(queries)
        for session in sessions:
            assert session["session_id"] in session_ids
            assert session["query"] in queries
            assert session["status"] == "planned"
            assert "timestamp" in session

    def test_atomic_file_write(self, temp_data_dir):
        """Test that file writes are atomic to prevent race conditions."""
        persistence = ResearchPersistence(data_dir=temp_data_dir)

        # Mock the file operations to simulate a race condition
        with patch('os.replace') as mock_replace, \
             patch('shutil.move') as mock_move, \
             patch('os.path.exists', return_value=True):

            # Simulate an error during the atomic replace
            mock_replace.side_effect = OSError("Simulated race condition")

            # Try to save data, which should handle the error
            with pytest.raises(OSError):
                persistence._save_session_data("test_session", {"test": "data"})

            # Verify that replace was called
            mock_replace.assert_called_once()
            # Move should not be called since we simulated that the file exists
            mock_move.assert_not_called()

    def test_handle_json_decode_error(self, temp_data_dir):
        """Test handling of JSON decode errors when loading session data."""
        persistence = ResearchPersistence(data_dir=temp_data_dir)

        # Create a file with invalid JSON
        session_id = "test_invalid_json"
        file_path = os.path.join(temp_data_dir, f"{session_id}.json")
        with open(file_path, "w") as f:
            f.write("This is not valid JSON")

        # Try to load the data
        data = persistence._load_session_data(session_id)
        assert data is None
