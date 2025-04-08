"""
Centralized configuration for the research agent.

This module provides a centralized place for configuration settings,
including model names, fallback options, and initialization functions.
"""

import logging
import importlib.util

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
    def get_writer_model(cls):
        """Get the writer model name with fallback."""
        if cls.WRITER_MODEL is None:
            logger.warning("Primary writer model is not available")
            logger.info(f"Falling back to {cls.WRITER_FALLBACK_MODEL}")
            return cls.WRITER_FALLBACK_MODEL
        return cls.WRITER_MODEL

    @classmethod
    def get_search_model(cls):
        """Get the search model name with fallback."""
        if cls.SEARCH_MODEL is None:
            logger.warning("Primary search model is not available")
            logger.info(f"Falling back to {cls.SEARCH_FALLBACK_MODEL}")
            return cls.SEARCH_FALLBACK_MODEL
        return cls.SEARCH_MODEL

    @classmethod
    def get_planner_model(cls):
        """Get the planner model name with fallback."""
        if cls.PLANNER_MODEL is None:
            logger.warning("Primary planner model is not available")
            logger.info(f"Falling back to {cls.PLANNER_FALLBACK_MODEL}")
            return cls.PLANNER_FALLBACK_MODEL
        return cls.PLANNER_MODEL


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
