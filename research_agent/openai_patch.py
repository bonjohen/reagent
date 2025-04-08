"""
Patch for OpenAI SDK to disable trace ingestion.
"""

import logging
import importlib.util
import sys
from types import ModuleType

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
        class DummyTraceClient:
            def __init__(self, *args, **kwargs):
                pass
            
            def capture(self, *args, **kwargs):
                pass
            
            def ingest(self, *args, **kwargs):
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
