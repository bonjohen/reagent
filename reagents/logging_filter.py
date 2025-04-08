"""
Logging filter to suppress specific log messages.
"""

import logging
import re

class HttpxTraceFilter(logging.Filter):
    """Filter to suppress httpx trace messages."""

    def __init__(self, pattern=r"(traces/ingest|POST https://api\.openai\.com/v1/traces)"):
        """Initialize the filter with a regex pattern to match against log messages."""
        super().__init__()
        self.pattern = re.compile(pattern)

    def filter(self, record):
        """Return False to suppress the log message if it matches the pattern."""
        if record.name == 'httpx' and self.pattern.search(record.getMessage()):
            return False
        return True

class OpenAITraceFilter(logging.Filter):
    """Filter to suppress all OpenAI trace-related messages."""

    def filter(self, record):
        """Return False to suppress the log message if it's related to OpenAI traces."""
        message = record.getMessage()
        if 'trace' in message.lower() and 'openai' in message.lower():
            return False
        return True

def apply_filters():
    """Apply logging filters to suppress specific messages."""
    # Get the root logger to apply filters globally
    root_logger = logging.getLogger()

    # Add our filters to it
    root_logger.addFilter(HttpxTraceFilter())
    root_logger.addFilter(OpenAITraceFilter())

    # Also apply to the httpx logger specifically
    httpx_logger = logging.getLogger('httpx')
    httpx_logger.addFilter(HttpxTraceFilter())

    # Set the httpx logger level to WARNING to suppress most messages
    httpx_logger.setLevel(logging.WARNING)
