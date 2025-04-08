"""
Logging configuration for the research agent.
"""

import logging
from reagents.logging_filter import apply_filters
from reagents.config import initialize_app

def configure_logging():
    """Configure logging for the research agent."""
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Configure formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)

    # Apply our custom filters to suppress specific messages
    apply_filters()

    # Initialize the application
    initialize_app()

    # You can add more loggers to suppress here if needed
    # For example:
    # logging.getLogger('urllib3').setLevel(logging.WARNING)
