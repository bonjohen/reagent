"""
Patch for OpenAI SDK to disable trace ingestion.

This utility module provides functionality to disable OpenAI's trace ingestion,
which can be useful during development or debugging to prevent unwanted telemetry.
It works by replacing the OpenAI trace client with a dummy implementation that does nothing.

This module is used by the logging_config.py module to disable tracing at application startup.
"""

import logging
import importlib.util

logger = logging.getLogger(__name__)

def disable_openai_tracing():
    """
    Disable OpenAI trace ingestion by patching the SDK.
    This is a more direct approach than filtering log messages.
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
