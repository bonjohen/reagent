"""Question generator agent for generating research questions.

This module contains the implementation of the question generator agent,
which generates diverse research questions based on a given topic.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from agents import Agent, Runner
from reagents.config import ModelConfig, QuestionGeneratorConfig

# Set up logging
logger = logging.getLogger(__name__)

# Constants
QUESTION_GENERATOR_MODEL = ModelConfig.PLANNER_MODEL
FALLBACK_MODEL = ModelConfig.PLANNER_FALLBACK_MODEL

class QuestionGeneratorResult:
    """Result from the question generator agent."""

    def __init__(self, questions: List[str], topic: str):
        """Initialize the question generator result.

        Args:
            questions: List of generated questions
            topic: The original research topic
        """
        self.questions = questions
        self.topic = topic

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.

        Returns:
            Dictionary representation of the result
        """
        return {
            "topic": self.topic,
            "questions": self.questions,
            "count": len(self.questions)
        }

def load_prompt_template() -> str:
    """Load the question generation prompt template from file.

    Returns:
        The prompt template as a string
    """
    try:
        with open("prompts/question_generation_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Question generation prompt template not found, using default")
        return DEFAULT_PROMPT

def deduplicate_questions(questions: List[str]) -> List[str]:
    """Remove duplicate or very similar questions from the list.

    Args:
        questions: List of questions to deduplicate

    Returns:
        Deduplicated list of questions
    """
    # Convert to lowercase for comparison
    lower_questions = [q.lower() for q in questions]

    # Remove exact duplicates while preserving original case
    unique_questions = []
    seen_lower = set()

    for i, lower_q in enumerate(lower_questions):
        if lower_q not in seen_lower:
            seen_lower.add(lower_q)
            unique_questions.append(questions[i])

    # Further deduplication for very similar questions could be implemented here
    # For now, we'll just return the exact-duplicate-free list
    return unique_questions

def extract_questions_from_response(response: str) -> List[str]:
    """Extract questions from the LLM response.

    Args:
        response: Raw response from the LLM

    Returns:
        List of extracted questions
    """
    # Try to extract a JSON array first
    try:
        import json
        # Check if the response is a JSON object with a questions field
        if response.strip().startswith('{') and 'questions' in response.lower():
            data = json.loads(response)
            if isinstance(data, dict) and 'questions' in data:
                questions = data['questions']
                if isinstance(questions, list):
                    return [q for q in questions if isinstance(q, str)]

        # Check if the response is a JSON array
        if response.strip().startswith('['):
            questions = json.loads(response)
            if isinstance(questions, list):
                return [q for q in questions if isinstance(q, str)]
    except json.JSONDecodeError:
        logger.debug("Response is not valid JSON, trying regex extraction")

    # If JSON parsing fails, try to extract questions using regex
    # Look for numbered questions (1. What is...? or 1) What is...?)
    numbered_pattern = r'(?:\d+[\.\)]\s*)([^?]+\?)'
    numbered_questions = re.findall(numbered_pattern, response)

    # Look for questions with bullet points (• What is...? or - What is...?)
    bullet_pattern = r'(?:[•\-\*]\s*)([^?]+\?)'
    bullet_questions = re.findall(bullet_pattern, response)

    # Look for standalone questions (What is...?)
    standalone_pattern = r'([A-Z][^?]+\?)'
    standalone_questions = re.findall(standalone_pattern, response)

    # Combine all found questions
    all_questions = numbered_questions + bullet_questions + standalone_questions

    # Clean up questions (remove leading/trailing whitespace)
    cleaned_questions = [q.strip() for q in all_questions]

    # Remove duplicates
    return deduplicate_questions(cleaned_questions)

def validate_questions(questions: List[str]) -> List[str]:
    """Validate and clean up the list of questions.

    Args:
        questions: List of questions to validate

    Returns:
        List of validated questions
    """
    valid_questions = []

    for q in questions:
        # Ensure the question ends with a question mark
        if not q.endswith('?'):
            q = q + '?'

        # Ensure the question starts with a capital letter
        if q and not q[0].isupper():
            q = q[0].upper() + q[1:]

        # Ensure the question is not too short
        if len(q) > 10:  # Arbitrary minimum length
            valid_questions.append(q)

    return valid_questions

async def generate_questions(topic: str, min_questions: int = QuestionGeneratorConfig.MIN_QUESTIONS, max_questions: int = QuestionGeneratorConfig.MAX_QUESTIONS) -> QuestionGeneratorResult:
    """Generate research questions for a given topic using the planner agent.

    Args:
        topic: The research topic
        min_questions: Minimum number of questions to generate (not used with new planner)
        max_questions: Maximum number of questions to generate (not used with new planner)

    Returns:
        QuestionGeneratorResult containing the generated questions
    """
    if not topic or not isinstance(topic, str):
        logger.error(f"Invalid topic: {topic}")
        return QuestionGeneratorResult([], str(topic) if topic else "")

    # Use the planner agent to generate questions directly
    try:
        logger.info(f"Generating questions for topic: {topic}")
        # Get the planner agent
        from reagents.agents.planner_agent import planner_agent, WebSearchPlan

        # Run the planner agent to get questions
        result = await Runner.run(planner_agent, topic)
        search_plan = WebSearchPlan.from_response(str(result.final_output), original_query=topic)

        # Extract questions from the search plan
        questions = [item.query for item in search_plan.searches]
        logger.info(f"Generated {len(questions)} questions for topic: {topic}")

        # Return the questions
        return QuestionGeneratorResult(questions, topic)
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        # Return an empty result if there's an error
        return QuestionGeneratorResult([], topic)



# Default prompt to use if the file is not found
DEFAULT_PROMPT = """
You are a research question generator. Your task is to generate {min_questions}-{max_questions} diverse and insightful research questions about the given topic.

Topic: {topic}

Generate questions that cover various aspects of the topic, including:
1. Definitions and basic concepts
2. Historical context and development
3. Current state and trends
4. Future prospects and challenges
5. Comparative analysis with related topics
6. Methodological approaches
7. Controversies and debates
8. Practical applications and implications
9. Ethical considerations
10. Economic and social impacts

Format your response as a numbered list of questions. Each question should be clear, focused, and end with a question mark.

Example format:
1. What is [topic] and how is it defined in different contexts?
2. How has [topic] evolved historically?
3. What are the current trends in [topic]?
...and so on.

Please generate {min_questions}-{max_questions} questions now.
"""

# Create the question generator agent with a valid model name
question_generator_agent = None  # Will be initialized when needed
