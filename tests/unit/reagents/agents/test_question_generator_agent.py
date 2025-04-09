"""Unit tests for the question generator agent."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from reagents.agents.question_generator_agent import (
    extract_questions_from_response,
    deduplicate_questions,
    validate_questions,
    generate_questions,
    QuestionGeneratorResult
)


class TestQuestionGeneratorAgent:
    """Tests for the question generator agent."""

    def test_deduplicate_questions(self):
        """Test deduplication of questions."""
        # Test with exact duplicates
        questions = [
            "What is graphene?",
            "How is graphene produced?",
            "What is graphene?",  # Duplicate
            "What are the applications of graphene?",
            "How is graphene produced?"  # Duplicate
        ]

        result = deduplicate_questions(questions)
        assert len(result) == 3
        assert "What is graphene?" in result
        assert "How is graphene produced?" in result
        assert "What are the applications of graphene?" in result

        # Test with case differences
        questions = [
            "What is graphene?",
            "what is graphene?",  # Same but different case
            "WHAT IS GRAPHENE?"  # Same but different case
        ]

        result = deduplicate_questions(questions)
        assert len(result) == 1

    def test_validate_questions(self):
        """Test validation of questions."""
        # Test with valid questions
        questions = [
            "What is graphene?",
            "How is graphene produced",  # Missing question mark
            "what are the applications of graphene?",  # Lowercase first letter
            "Too short"  # Too short
        ]

        result = validate_questions(questions)
        assert len(result) == 3
        assert "What is graphene?" in result
        assert "How is graphene produced?" in result  # Question mark added
        assert "What are the applications of graphene?" in result  # First letter capitalized
        assert "Too short" not in result  # Too short, should be filtered out

    def test_extract_questions_from_response_json(self):
        """Test extraction of questions from JSON response."""
        # Test with valid JSON array
        json_array = json.dumps([
            "What is graphene?",
            "How is graphene produced?",
            "What are the applications of graphene?"
        ])

        result = extract_questions_from_response(json_array)
        assert len(result) == 3

        # Test with valid JSON object with questions field
        json_obj = json.dumps({
            "questions": [
                "What is graphene?",
                "How is graphene produced?",
                "What are the applications of graphene?"
            ]
        })

        result = extract_questions_from_response(json_obj)
        assert len(result) == 3

    def test_extract_questions_from_response_text(self):
        """Test extraction of questions from text response."""
        # Test with numbered questions
        text = """
        Here are some questions about graphene:

        1. What is graphene?
        2. How is graphene produced?
        3. What are the applications of graphene?
        """

        result = extract_questions_from_response(text)
        # Check that the expected questions are in the result
        assert "What is graphene?" in result
        assert "How is graphene produced?" in result
        assert "What are the applications of graphene?" in result

        # Test with bullet points
        text = """
        Here are some questions about graphene:

        • What is graphene?
        - How is graphene produced?
        * What are the applications of graphene?
        """

        result = extract_questions_from_response(text)
        # Check that the expected questions are in the result
        assert "What is graphene?" in result
        assert "How is graphene produced?" in result
        assert "What are the applications of graphene?" in result

        # Test with standalone questions
        text = """
        What is graphene? How is graphene produced? What are the applications of graphene?
        """

        result = extract_questions_from_response(text)
        # Check that the expected questions are in the result
        assert "What is graphene?" in result
        assert "How is graphene produced?" in result
        assert "What are the applications of graphene?" in result

    @pytest.mark.asyncio
    async def test_generate_questions(self):
        """Test generation of questions."""
        # Mock the Runner.run method for the planner
        with patch('agents.Runner.run') as mock_run, \
             patch('reagents.agents.planner_agent.WebSearchPlan.from_response') as mock_from_response:
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

            # Set up the mock for WebSearchPlan.from_response
            from reagents.agents.planner_agent import WebSearchPlan, WebSearchItem
            search_plan = WebSearchPlan(
                searches=[
                    WebSearchItem(query="What is graphene?"),
                    WebSearchItem(query="How is graphene produced?"),
                    WebSearchItem(query="What are the applications of graphene?")
                ]
            )
            mock_from_response.return_value = search_plan

            # Call the function
            result = await generate_questions("graphene")

            # Check the result
            assert isinstance(result, QuestionGeneratorResult)
            assert result.topic == "graphene"
            assert len(result.questions) == 3
            assert "What is graphene?" in result.questions

            # Check that the mocks were called
            mock_run.assert_called_once()
            mock_from_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_questions_empty_topic(self):
        """Test generation of questions with empty topic."""
        # Call the function with empty topic
        result = await generate_questions("")

        # Check the result
        assert isinstance(result, QuestionGeneratorResult)
        assert result.topic == ""
        assert len(result.questions) == 0

    @pytest.mark.asyncio
    async def test_generate_questions_error(self):
        """Test generation of questions with error."""
        # Mock the Runner.run method to raise an exception
        with patch('agents.Runner.run', side_effect=Exception("Test error")):
            # Call the function
            result = await generate_questions("graphene")

            # Check the result
            assert isinstance(result, QuestionGeneratorResult)
            assert result.topic == "graphene"
            assert len(result.questions) == 0

    @pytest.mark.asyncio
    async def test_generate_questions_with_planner(self):
        """Test generation of questions using the planner agent."""
        # Mock the Runner.run method for the planner
        with patch('agents.Runner.run') as mock_run, \
             patch('reagents.agents.planner_agent.WebSearchPlan.from_response') as mock_from_response:
            # Set up the mock for the planner
            planner_result = MagicMock()
            planner_result.final_output = json.dumps({
                "searches": [
                    "What is graphene?",
                    "How is graphene produced?",
                    "What are the applications of graphene?",
                    "What are the latest advancements in graphene research?",
                    "How does graphene compare to other materials?"
                ]
            })
            mock_run.return_value = planner_result

            # Set up the mock for WebSearchPlan.from_response
            from reagents.agents.planner_agent import WebSearchPlan, WebSearchItem
            search_plan = WebSearchPlan(
                searches=[
                    WebSearchItem(query="What is graphene?"),
                    WebSearchItem(query="How is graphene produced?"),
                    WebSearchItem(query="What are the applications of graphene?"),
                    WebSearchItem(query="What are the latest advancements in graphene research?"),
                    WebSearchItem(query="How does graphene compare to other materials?")
                ]
            )
            mock_from_response.return_value = search_plan

            # Call the function
            result = await generate_questions("graphene")

            # Check the result
            assert isinstance(result, QuestionGeneratorResult)
            assert result.topic == "graphene"
            assert len(result.questions) == 5
            assert "What is graphene?" in result.questions

            # Check that the mocks were called
            mock_run.assert_called_once()
            mock_from_response.assert_called_once()
