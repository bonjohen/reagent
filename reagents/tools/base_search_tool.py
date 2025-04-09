"""
Base search tool class for common search functionality.
"""

import logging
import aiohttp
from typing import Dict, Any, List, Optional, Tuple

# Import configuration
from reagents.config import AppConstants

# Set up logging
logger = logging.getLogger(__name__)

class BaseSearchTool:
    """Base class for search tools with common functionality."""

    def __init__(self, api_key: Optional[str] = None, api_name: str = ""):
        """Initialize the base search tool.

        Args:
            api_key: API key for the search service
            api_name: Name of the API service (for logging)
        """
        self.api_key = api_key
        self.api_name = api_name
        self.endpoint = ""  # To be set by subclasses
        self.error_state = False
        self.stop_after_first_error = False
        self.last_urls = []
        self.last_search_results = []

    def set_error_state(self, state: bool) -> None:
        """Set the error state of the search tool.

        Args:
            state: True if the search tool is in an error state, False otherwise
        """
        self.error_state = state
        if state:
            logger.warning(f"{self.api_name} search tool is now in error state. No more searches will be performed.")

    def has_error(self) -> bool:
        """Check if the search tool is in an error state.

        Returns:
            True if the search tool is in an error state, False otherwise
        """
        return self.error_state

    def _validate_api_key(self, min_length: int = 20, prefix: Optional[str] = None,
                         check_alphanumeric: bool = True) -> None:
        """Common API key validation logic.

        Args:
            min_length: Minimum expected length of the API key
            prefix: Expected prefix for the API key (if any)
            check_alphanumeric: Whether to check if the key is alphanumeric
        """
        if not self.api_key:
            return

        # Check for proper prefix if specified
        if prefix and not self.api_key.startswith(prefix):
            logger.warning(f"{self.api_name} API key does not start with '{prefix}' prefix - this may cause issues")

        # Check for minimum length
        if len(self.api_key) < min_length:
            logger.warning(f"{self.api_name} API key appears to be too short: {len(self.api_key)} chars")

        # Check for valid characters
        if check_alphanumeric:
            key_body = self.api_key[len(prefix):] if prefix and self.api_key.startswith(prefix) else self.api_key
            if not key_body.isalnum():
                logger.warning(f"{self.api_name} API key contains invalid characters - this may cause issues")

    async def _make_api_request(self, endpoint: str, headers: Dict[str, str],
                               params: Dict[str, Any], query: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Common API request logic with error handling.

        Args:
            endpoint: API endpoint URL
            headers: HTTP headers for the request
            params: Request parameters/payload
            query: The search query (for error messages)

        Returns:
            Tuple of (response_data, error_message)
            If successful, response_data contains the API response and error_message is None
            If failed, response_data is None and error_message contains the error
        """
        # Create the session outside the try block to ensure it's always closed
        session = None
        try:
            logger.info(f"Performing {self.api_name} search for: {query}")
            # Also log to console for better visibility
            print(f"Performing {self.api_name} search for: {query}")
            # Use a default timeout of 30 seconds
            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
            async with session.post(endpoint, headers=headers, json=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"{self.api_name} API error: {response.status} - {error_text}")

                    # Handle authentication errors (401)
                    if response.status == 401:
                        error_message = f"ERROR: {self.api_name} API authentication failed. Invalid API key. Please check your {self.api_name} API key and try again."
                        # Set the error state to prevent further searches
                        self.set_error_state(True)
                        return None, f"[{error_message}]"

                    # Handle rate limit errors (429) - common for Tavily when out of tokens
                    elif response.status == 429:
                        error_message = f"ERROR: {self.api_name} API returned 'Too Many Requests'. Your {self.api_name} account has likely run out of credits or hit rate limits. Please add more credits to your {self.api_name} account or try again later."
                        # Set the error state to prevent further searches
                        self.set_error_state(True)
                        # This is a critical error that should stop all further searches
                        self.stop_after_first_error = True
                        return None, f"[{error_message}]"

                    # Handle payment required errors (402)
                    elif response.status == 402:
                        error_message = f"ERROR: {self.api_name} API returned payment required. Your {self.api_name} account requires payment or has run out of credits. Please check your account status."
                        # Set the error state to prevent further searches
                        self.set_error_state(True)
                        # This is a critical error that should stop all further searches
                        self.stop_after_first_error = True
                        return None, f"[{error_message}]"

                    # Handle bad request errors (400) - could be "Not enough credits" for Serper
                    elif response.status == 400 and "Not enough credits" in error_text:
                        error_message = f"ERROR: {self.api_name} API returned 'Not enough credits'. Your {self.api_name} account has run out of credits. Please add more credits to your {self.api_name} account or use a different API key."
                        # Set the error state to prevent further searches
                        self.set_error_state(True)
                        # This is a critical error that should stop all further searches
                        self.stop_after_first_error = True
                        return None, f"[{error_message}]"

                    # Generic error for other status codes
                    return None, f"[Search for '{query}' failed: API returned status {response.status}]"

                data = await response.json()
                return data, None
        except Exception as e:
            logger.error(f"Error during {self.api_name} search: {str(e)}")
            return None, f"[Search for '{query}' failed: {str(e)}]"
        finally:
            # Ensure the session is closed
            if session and not session.closed:
                await session.close()

    def _format_search_results(self, results: List[str], query: str,
                              truncated: bool = False, max_chars: int = 8000) -> str:
        """Common search result formatting logic.

        Args:
            results: List of formatted search result strings
            query: The search query
            truncated: Whether the results were truncated
            max_chars: Maximum characters allowed in the output

        Returns:
            Formatted search results as a string
        """
        if not results:
            return f"No results found for query: {query}"

        header = f"Search results for '{query}':\n\n"
        truncation_notice = "\n[Note: Search results were truncated due to size limits]"

        # Basic formatting
        result_text = header + "\n".join(results)

        # Add truncation notice if needed
        if truncated:
            result_text += truncation_notice

        # Ensure we don't exceed max_chars
        if len(result_text) > max_chars:
            available_space = max_chars - len(header) - len(truncation_notice)
            if available_space > 0:
                joined_results = "\n".join(results)
                result_text = header + joined_results[:available_space] + truncation_notice
            else:
                result_text = (header + truncation_notice)[:max_chars]

        return result_text
