"""
Centralized configuration for the research agent.

This module provides a centralized place for configuration settings,
including model names, fallback options, and initialization functions.
"""

import logging
import importlib.util
import os
from typing import Optional

# Set up logging
logger = logging.getLogger(__name__)

class ModelConfig:
    """Configuration for OpenAI models used in the application."""

    # Primary models
    WRITER_MODEL = "gpt-3.5-turbo"
    SEARCH_MODEL = "gpt-3.5-turbo"
    PLANNER_MODEL = "gpt-3.5-turbo"

    # Fallback models (used if primary models are unavailable)
    WRITER_FALLBACK_MODEL = "gpt-3.5-turbo-0125"
    SEARCH_FALLBACK_MODEL = "gpt-3.5-turbo-0125"
    PLANNER_FALLBACK_MODEL = "gpt-3.5-turbo-0125"

    @classmethod
    def get_model_with_fallback(cls, model_type: str):
        """Get a model name with fallback.

        Args:
            model_type: One of "writer", "search", or "planner"

        Returns:
            The model name to use, falling back to the fallback model if needed

        Raises:
            ValueError: If an unknown model type is provided
        """
        model_attr = f"{model_type.upper()}_MODEL"
        fallback_attr = f"{model_type.upper()}_FALLBACK_MODEL"

        if not hasattr(cls, model_attr) or not hasattr(cls, fallback_attr):
            raise ValueError(f"Unknown model type: {model_type}")

        primary_model = getattr(cls, model_attr)
        fallback_model = getattr(cls, fallback_attr)

        if primary_model is None:
            logger.warning(f"Primary {model_type} model is not available")
            logger.info(f"Falling back to {fallback_model}")
            return fallback_model
        return primary_model

    @classmethod
    def get_writer_model(cls):
        """Get the writer model name with fallback."""
        return cls.get_model_with_fallback("writer")

    @classmethod
    def get_search_model(cls):
        """Get the search model name with fallback."""
        return cls.get_model_with_fallback("search")

    @classmethod
    def get_planner_model(cls):
        """Get the planner model name with fallback."""
        return cls.get_model_with_fallback("planner")


def disable_openai_tracing():
    """Disable OpenAI trace ingestion by patching the SDK.

    This is a more direct approach than filtering log messages.

    Returns:
        bool: True if tracing was successfully disabled, False otherwise
    """
    try:
        # Check if openai module is available
        if importlib.util.find_spec("openai") is None:
            logger.warning("OpenAI module not found, cannot disable tracing")
            return False

        # Import the openai module
        import openai

        # Create a dummy trace client that does nothing
        # The unused parameters are intentional as they need to match the signature of the original methods
        class DummyTraceClient:
            def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
                pass

            def capture(self, *args, **kwargs):  # pylint: disable=unused-argument
                pass

            def ingest(self, *args, **kwargs):  # pylint: disable=unused-argument
                pass

        # Try to find the trace module in the openai package
        if hasattr(openai, "_trace"):
            # Replace the trace client with our dummy client
            openai._trace.client = DummyTraceClient()
            logger.info("Successfully disabled OpenAI trace ingestion")
            return True
        else:
            logger.warning("Could not find _trace module in OpenAI SDK")
            return False

    except Exception as e:
        logger.error(f"Error disabling OpenAI tracing: {str(e)}")
        return False


# Application constants
class AppConstants:
    """Application-wide constants."""

    # File paths and directories
    DEFAULT_DATA_DIR = "research_data"

    # API limits
    MAX_SEARCH_RESULTS = 10
    MAX_SEARCH_DEPTH = "advanced"  # Can be "basic" or "advanced"

    # Content limits
    MAX_REPORT_LENGTH = 10000  # Maximum length of a report in characters
    MAX_SEARCH_RESULT_LENGTH = 8000  # Maximum combined length of search results


# Question generator configuration
class QuestionGeneratorConfig:
    """Configuration for the question generator."""

    # Number of questions to generate
    MIN_QUESTIONS = 40
    MAX_QUESTIONS = 50

    # Whether to use search results to generate questions
    USE_SEARCH_RESULTS = True

    # Timeouts
    API_TIMEOUT_SECONDS = 30  # Timeout for API calls

    # Retry configuration
    MAX_RETRIES = 3  # Maximum number of retries for API calls
    RETRY_DELAY_SECONDS = 2  # Delay between retries


# Environment variable configuration
class EnvironmentConfig:
    """Centralized access to environment variables."""

    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        """Get the OpenAI API key from environment variables."""
        return os.environ.get("OPENAI_API_KEY")

    @staticmethod
    def get_serper_api_key() -> Optional[str]:
        """Get the Serper API key from environment variables."""
        return os.environ.get("SERPER_API_KEY")

    @staticmethod
    def get_tavily_api_key() -> Optional[str]:
        """Get the Tavily API key from environment variables."""
        return os.environ.get("TAVILY_API_KEY")

    @staticmethod
    def has_search_api_keys() -> bool:
        """Check if any search API keys are available."""
        return bool(EnvironmentConfig.get_serper_api_key() or EnvironmentConfig.get_tavily_api_key())


def initialize_app():
    """Initialize the application.

    This function performs all necessary initialization tasks for the application,
    including disabling OpenAI tracing and any other setup tasks.

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    success = True

    # Disable OpenAI tracing
    if not disable_openai_tracing():
        logger.warning("Failed to disable OpenAI tracing, but continuing anyway")
        success = False

    # Add any other initialization tasks here

    return success
