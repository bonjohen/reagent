import traceback
import logging
from typing import Optional

def format_error(e: Exception, context: Optional[str] = None) -> str:
    """
    Format an exception with detailed information for better debugging.
    Sanitizes the error message to avoid exposing sensitive information.

    Args:
        e: The exception to format
        context: Optional context information about where the error occurred

    Returns:
        A sanitized formatted error message with actionable advice
    """
    error_type = type(e).__name__
    error_message = str(e)
    tb = traceback.format_exc()

    # Log the full traceback for debugging purposes
    logging.debug(f"Detailed error traceback:\n{tb}")

    # Create a user-friendly error message with actionable advice
    if context:
        base_message = f"Error during {context}: {error_type}"
    else:
        base_message = f"Error: {error_type}"

    # Add specific advice based on the error type
    advice = get_error_advice(error_type, error_message, context)

    # Combine the base message and advice
    formatted_error = f"{base_message}\n{advice}"

    return formatted_error

def get_error_advice(error_type: str, error_message: str, context: Optional[str] = None) -> str:
    """
    Get specific advice for different types of errors.

    Args:
        error_type: The type of the exception
        error_message: The error message
        context: Optional context information about where the error occurred

    Returns:
        Actionable advice for the user
    """
    # API-related errors
    if error_type == "AuthenticationError" or "InvalidAPIKey" in error_type:
        return "Please check that your API key is valid and properly set in your environment variables."

    elif error_type == "RateLimitError":
        return "You've hit the rate limit for the API. Please wait a moment and try again, or consider upgrading your API plan."

    elif error_type == "APIConnectionError" or error_type == "ConnectionError":
        return "Could not connect to the API. Please check your internet connection and try again."

    # File-related errors
    elif error_type == "FileNotFoundError":
        return "A required file could not be found. Please check that all files are in the correct locations."

    elif error_type == "PermissionError":
        return "Permission denied when accessing a file. Please check your file permissions."

    # JSON-related errors
    elif error_type == "JSONDecodeError":
        if context and "report" in context:
            return "Could not parse the report data. This is usually a temporary issue. Please try again or simplify your research topic."
        else:
            return "Could not parse JSON data. The file may be corrupted. Try running the repair script: python -m utils.repair_session_files"

    # Value errors
    elif error_type == "ValueError":
        if "API key" in error_message:
            return "Invalid API key format. Please check your API key and ensure it's correctly set in your environment variables."
        else:
            return "Invalid value provided. Please check your input and try again."

    # Type errors
    elif error_type == "TypeError":
        return "Unexpected data type encountered. This may be due to corrupted data or an incompatible API response."

    # Generic advice for other errors
    else:
        return "For more information, please check the documentation or run with debug logging enabled."
