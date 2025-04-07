import traceback
from typing import Optional

def format_error(e: Exception, context: Optional[str] = None) -> str:
    """
    Format an exception with detailed information for better debugging.
    Sanitizes the error message to avoid exposing sensitive information.

    Args:
        e: The exception to format
        context: Optional context information about where the error occurred

    Returns:
        A sanitized formatted error message
    """
    error_type = type(e).__name__
    tb = traceback.format_exc()

    # Create a sanitized error message that doesn't include potentially sensitive details
    if context:
        formatted_error = f"A {error_type} occurred during {context}"
    else:
        formatted_error = f"A {error_type} occurred"

    # Add traceback for debugging (console only, not included in returned message)
    print(f"\nDetailed error traceback:\n{tb}")

    return formatted_error
