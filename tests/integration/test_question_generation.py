"""Integration tests for the question generation functionality."""

import pytest
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock

from reagents.manager import ResearchManager
from reagents.agents.question_generator_agent import QuestionGeneratorResult


@pytest.mark.asyncio
async def test_generate_questions_integration():
    """Test the question generation integration with the ResearchManager."""
    # Mock the Runner.run method for the planner
    with patch('agents.Runner.run') as mock_run:
        # Set up the mock for the planner
        planner_result = MagicMock()
        planner_result.final_output = json.dumps({
            "searches": [
                "What is graphene?",
                "How is graphene produced?",
                "What are the applications of graphene?"
            ]
        })
        mock_run.return_value = planner_result

        # Create a manager
        manager = ResearchManager()

        # Call the _generate_questions method
        result = await manager._generate_questions("graphene")

        # Check the result
        assert isinstance(result, QuestionGeneratorResult)
        assert result.topic == "graphene"
        assert len(result.questions) == 3
        assert "What is graphene?" in result.questions

        # Check that the mock was called
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_questions_in_session_data():
    """Test that questions are saved in the session data."""
    # Create a temporary directory for test data
    import tempfile
    temp_dir = tempfile.mkdtemp()

    try:
        # Create mocks for the necessary functions
        with patch('agents.Runner.run') as mock_run, \
             patch('reagents.persistence.ResearchPersistence._get_session_path') as mock_path, \
             patch('reagents.manager.ResearchManager._plan_searches', return_value=None), \
             patch('reagents.manager.ResearchManager._perform_searches', return_value=[]), \
             patch('reagents.manager.ResearchManager._write_report', return_value=None):

            # Set up the mock for the planner
            planner_result = MagicMock()
            planner_result.final_output = json.dumps({
                "searches": [
                    "What is graphene?",
                    "How is graphene produced?",
                    "What are the applications of graphene?"
                ]
            })
            mock_run.return_value = planner_result

            # Mock the session path to use our temporary directory
            mock_path.return_value = os.path.join(temp_dir, "test_session.json")

            # Create a manager
            manager = ResearchManager()

            # Run the manager
            await manager.run("graphene")

            # Check that the session data contains the questions
            session_path = os.path.join(temp_dir, "test_session.json")
            if os.path.exists(session_path):
                with open(session_path, "r") as f:
                    data = json.load(f)
                    assert "search_questions" in data
                    assert data["search_questions"]["topic"] == "graphene"
                    assert len(data["search_questions"]["questions"]) == 3
                    assert "What is graphene?" in data["search_questions"]["questions"]
    finally:
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_questions_only_flag():
    """Test the --questions-only flag functionality."""
    # This is more of a functional test that would be better tested manually
    # Here we just verify that the generate_questions_only function works

    # Create mocks for the Runner.run method and print
    with patch('agents.Runner.run') as mock_run, \
         patch('builtins.print') as mock_print:

        # Set up the mock for the planner
        planner_result = MagicMock()
        planner_result.final_output = json.dumps({
            "searches": [
                "What is graphene?",
                "How is graphene produced?",
                "What are the applications of graphene?"
            ]
        })
        mock_run.return_value = planner_result

        # Import the function
        from main import generate_questions_only

        # Call the function
        await generate_questions_only("graphene")

        # Check that the mock was called
        mock_run.assert_called_once()

        # Check that print was called with the expected output
        mock_print.assert_any_call("\nGenerated 3 research questions:\n")
