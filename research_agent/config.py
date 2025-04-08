"""
Centralized configuration for the research agent.

This module provides a centralized place for configuration settings,
including model names and fallback options.
"""

import logging

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
