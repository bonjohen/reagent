"""
Custom search tools using Serper and Tavily APIs.
These provide more reliable search functionality than the default WebSearchTool.
"""

import logging
import aiohttp
import re
from typing import Optional, Dict, Any, List
from urllib.parse import quote_plus

from reagents.config import EnvironmentConfig, AppConstants
from reagents.tools.base_search_tool import BaseSearchTool

# Set up logging
logger = logging.getLogger(__name__)

class SerperSearchTool(BaseSearchTool):
    """Search tool that uses the Serper API to get Google search results."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Serper search tool.

        Args:
            api_key: Serper API key. If not provided, will try to get from environment.
        """
        super().__init__(api_key or EnvironmentConfig.get_serper_api_key(), "Serper")
        self.endpoint = "https://google.serper.dev/search"

        # Validate API key format
        if self.api_key:
            self._validate_api_key()

    async def search(self, query: str, num_results: int = AppConstants.MAX_SEARCH_RESULTS) -> str:
        """Perform a search using the Serper API.

        Args:
            query: The search query
            num_results: Number of results to return

        Returns:
            A string containing the search results
        """
        if not self.api_key:
            logger.error("Serper API key not found. Search functionality will be limited.")
            return f"[Search for '{query}' failed: No Serper API key provided]"

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": num_results
        }

        # Use the base class method to make the API request
        data, error = await self._make_api_request(self.endpoint, headers, payload, query)
        if error:
            return error

        # Format the results
        return self._format_results(data, query)

    def _format_results(self, data: Dict[str, Any], query: str, max_chars: int = 16000) -> str:
        """Format the search results into a readable string with size limits.

        Args:
            data: The JSON response from Serper API
            query: The original search query
            max_chars: Maximum number of characters in the formatted results

        Returns:
            A formatted string with search results, truncated if necessary
        """
        # Validate that data is a dictionary
        if not isinstance(data, dict):
            logger.error(f"Serper API returned non-dictionary data: {type(data).__name__}")
            return f"[Search error: Serper API returned non-dictionary data: {type(data).__name__}]"

        results = []
        total_length = 0
        truncated = False

        # Add organic results
        if "organic" in data and isinstance(data["organic"], list):
            for item in data["organic"]:
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dictionary item in organic results: {type(item).__name__}")
                    continue

                title = item.get("title", "No title")
                link = item.get("link", "")
                snippet = item.get("snippet", "No description available")

                # Ensure all fields are strings
                if not isinstance(title, str):
                    title = str(title)
                if not isinstance(link, str):
                    link = str(link)
                if not isinstance(snippet, str):
                    snippet = str(snippet)

                # Limit the length of individual fields
                if len(title) > 100:
                    title = title[:97] + "..."
                if len(snippet) > 300:
                    snippet = snippet[:297] + "..."

                result_item = f"Title: {title}\nURL: {link}\nDescription: {snippet}\n"

                # Check if adding this item would exceed the max_chars limit
                if total_length + len(result_item) > max_chars:
                    truncated = True
                    break

                results.append(result_item)
                total_length += len(result_item)
        elif "organic" in data and not isinstance(data["organic"], list):
            logger.error(f"Serper API returned non-list organic results: {type(data['organic']).__name__}")
            results.append(f"[Error: Serper API returned non-list organic results: {type(data['organic']).__name__}]")
            total_length += len(results[-1])

        # Add knowledge graph if available
        if "knowledgeGraph" in data and not truncated:
            kg = data["knowledgeGraph"]

            # Validate that knowledge graph is a dictionary
            if not isinstance(kg, dict):
                logger.debug(f"Skipping non-dictionary knowledge graph: {type(kg).__name__}")
            else:
                title = kg.get("title", "")
                description = kg.get("description", "")

                # Ensure fields are strings
                if not isinstance(title, str):
                    title = str(title)
                if not isinstance(description, str):
                    description = str(description)

                # Limit the length of title and description
                if len(title) > 100:
                    title = title[:97] + "..."
                if len(description) > 300:
                    description = description[:297] + "..."

                if title and description:
                    kg_text = f"Knowledge Graph: {title} - {description}\n"

                    # Check if adding knowledge graph would exceed the limit
                    if total_length + len(kg_text) <= max_chars:
                        results.append(kg_text)
                        total_length += len(kg_text)
                    else:
                        truncated = True

        # Add related searches if available
        if "relatedSearches" in data and not truncated:
            related_searches = data["relatedSearches"]

            # Validate that related searches is a list
            if not isinstance(related_searches, list):
                logger.warning(f"Skipping non-list related searches: {type(related_searches).__name__}")
            elif related_searches:  # Only process if the list is not empty
                # Ensure all items are strings and limit to 5 items
                valid_searches = []
                for search in related_searches[:5]:  # Maximum 5 related searches
                    if not isinstance(search, str):
                        search = str(search)
                    valid_searches.append(search)

                if valid_searches:
                    related = "Related searches: " + ", ".join(valid_searches) + "\n"

                    # Check if adding related searches would exceed the limit
                    if total_length + len(related) <= max_chars:
                        results.append(related)
                        total_length += len(related)
                    else:
                        truncated = True

        # If no results found
        if not results:
            return f"No results found for query: {query}"

        # Use the base class method to format the results
        return self._format_search_results(results, query, truncated, max_chars=AppConstants.MAX_SEARCH_RESULT_LENGTH)


class TavilySearchTool(BaseSearchTool):
    """Search tool that uses the Tavily API for web search."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Tavily search tool.

        Args:
            api_key: Tavily API key. If not provided, will try to get from environment.
        """
        super().__init__(api_key or EnvironmentConfig.get_tavily_api_key(), "Tavily")
        self.endpoint = "https://api.tavily.com/search"

        # Validate API key format
        if self.api_key:
            self._validate_api_key(min_length=20, prefix="tvly-", check_alphanumeric=True)

    async def search(self, query: str, search_depth: str = AppConstants.MAX_SEARCH_DEPTH, max_results: int = AppConstants.MAX_SEARCH_RESULTS) -> str:
        """Perform a search using the Tavily API.

        Args:
            query: The search query
            search_depth: Either "basic" or "advanced"
            max_results: Maximum number of results to return

        Returns:
            A string containing the search results
        """
        if not self.api_key:
            logger.error("Tavily API key not found. Search functionality will be limited.")
            return f"[Search for '{query}' failed: No Tavily API key provided]"

        # Set up headers with API key
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }

        # Set up parameters (without the API key)
        params = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": "true",  # Using string "true" instead of boolean True
            "include_domains": [],
            "exclude_domains": []
        }

        # Use the base class method to make the API request
        data, error = await self._make_api_request(self.endpoint, headers, params, query)
        if error:
            return error

        # Format the results
        return self._format_results(data, query)

    def _format_results(self, data: Dict[str, Any], query: str, max_chars: int = 8000) -> str:
        """Format the search results into a readable string with size limits.

        Args:
            data: The JSON response from Tavily API
            query: The original search query
            max_chars: Maximum number of characters in the formatted results

        Returns:
            A formatted string with search results, truncated if necessary
        """
        # Validate that data is a dictionary
        if not isinstance(data, dict):
            logger.error(f"Tavily API returned non-dictionary data: {type(data).__name__}")
            return f"[Search error: Tavily API returned non-dictionary data: {type(data).__name__}]"

        results = []
        total_length = 0
        truncated = False

        # Calculate the header length to reserve space
        header = f"Search results for '{query}':\n\n"
        truncation_notice = "\n[Note: Search results were truncated due to size limits]"
        reserved_space = len(header) + len(truncation_notice)
        effective_max_chars = max_chars - reserved_space

        # Add the answer if available
        if "answer" in data and effective_max_chars > 0:
            answer = data["answer"]

            # Ensure answer is a string
            if not isinstance(answer, str):
                logger.warning(f"Converting non-string answer to string: {type(answer).__name__}")
                answer = str(answer)

            if answer:  # Only process if answer is not empty
                # Limit answer length based on available space
                max_answer_length = min(500, effective_max_chars - 20)  # Leave some space for formatting
                if len(answer) > max_answer_length:
                    answer = answer[:max_answer_length-3] + "..."

                answer_text = f"Summary: {answer}\n"
                if total_length + len(answer_text) <= effective_max_chars:
                    results.append(answer_text)
                    total_length += len(answer_text)
                else:
                    truncated = True

        # Add search results
        if "results" in data:
            results_data = data["results"]

            # Validate that results is a list
            if not isinstance(results_data, list):
                logger.warning(f"Skipping non-list results: {type(results_data).__name__}")
                results.append(f"[Error: Tavily API returned non-list results: {type(results_data).__name__}]")
                total_length += len(results[-1])
            else:
                for item in results_data:
                    # Validate that item is a dictionary
                    if not isinstance(item, dict):
                        logger.warning(f"Skipping non-dictionary result item: {type(item).__name__}")
                        continue

                    title = item.get("title", "No title")
                    url = item.get("url", "")
                    content = item.get("content", "No content available")

                    # Ensure all fields are strings
                    if not isinstance(title, str):
                        title = str(title)
                    if not isinstance(url, str):
                        url = str(url)
                    if not isinstance(content, str):
                        content = str(content)

                    # Limit the length of individual fields
                    if len(title) > 100:
                        title = title[:97] + "..."
                    if len(content) > 300:
                        content = content[:297] + "..."

                    result_item = f"Title: {title}\nURL: {url}\nContent: {content}\n"

                    # Check if adding this item would exceed the max_chars limit
                    if total_length + len(result_item) > max_chars:
                        truncated = True
                        break

                    results.append(result_item)
                    total_length += len(result_item)

        # If no results found
        if not results:
            return f"No results found for query: {query}"

        # Use the base class method to format the results
        return self._format_search_results(results, query, truncated, max_chars=max_chars)


class DuckDuckGoSearchTool(BaseSearchTool):
    """Search tool that uses DuckDuckGo for web search without requiring an API key."""

    def __init__(self):
        """Initialize the DuckDuckGo search tool."""
        super().__init__(None, "DuckDuckGo")
        self.endpoint = "https://duckduckgo.com/html/"
        self.last_urls = []
        self.last_search_results = []

    async def check_credits(self) -> Dict[str, Any]:
        """Check the available credits for DuckDuckGo.

        DuckDuckGo doesn't require credits, so this always returns unlimited.

        Returns:
            A dictionary indicating unlimited credits
        """
        return {"credits_remaining": "unlimited", "status": "ok"}

    async def search(self, query: str, max_results: int = 5) -> str:
        """Perform a search using DuckDuckGo.

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            A string containing the search results or an error message
        """
        # Construct the search URL
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        # Set up headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        logger.info(f"Searching DuckDuckGo for: {query}")

        try:
            # Use aiohttp to make the request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"DuckDuckGo search error: {response.status} - {error_text}")

                        # Set the error state to prevent further searches
                        self.set_error_state(True)

                        # For 403 errors (common with DuckDuckGo), indicate that automated access is blocked
                        if response.status == 403:
                            error_message = f"ERROR: DuckDuckGo is blocking automated access. Search for '{query}' failed with status 403 Forbidden."
                            # This is a critical error that should stop all further searches
                            self.stop_after_first_error = True
                        else:
                            error_message = f"ERROR: Search for '{query}' failed with status {response.status}."

                        return f"[{error_message}]"

                    # Get the HTML content
                    html = await response.text()

                    # Extract search results using regex
                    results = []
                    self.last_urls = []
                    self.last_search_results = []

                    # Find titles
                    title_matches = re.findall(r'<h2 class="result__title[^>]*>\s*<a[^>]*>(.*?)</a>', html)
                    # Find URLs
                    url_matches = re.findall(r'<h2 class="result__title[^>]*>\s*<a[^>]*href="([^"]+)"', html)
                    # Find snippets
                    snippet_matches = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html)

                    # Process the results
                    for i in range(min(max_results, len(title_matches))):
                        if i < len(title_matches) and i < len(url_matches):
                            # Clean the title and snippet
                            title = re.sub(r'<.*?>', '', title_matches[i]).strip()
                            url = url_matches[i]
                            snippet = re.sub(r'<.*?>', '', snippet_matches[i]).strip() if i < len(snippet_matches) else ""

                            # Add to results list for formatting
                            result_text = f"Title: {title}\nURL: {url}\nContent: {snippet}"
                            results.append(result_text)

                            # Store the URL for later use
                            self.last_urls.append(url)

                            # Store the detailed search result for later use
                            self.last_search_results.append({
                                "title": title,
                                "url": url,
                                "content": snippet
                            })

                    # If no results found
                    if not results:
                        logger.warning(f"No results found for query: {query}")
                        return f"No results found for query: {query}"

                    # Format the results
                    return self._format_search_results(results, query, False)
        except Exception as e:
            logger.error(f"Error during DuckDuckGo search: {str(e)}")
            # Set the error state to prevent further searches
            self.set_error_state(True)
            return f"[ERROR: Search for '{query}' failed: {str(e)}]"


# Factory function to get the appropriate search tool based on available API keys
def get_search_tool():
    """Get the best available search tool based on available API keys."""
    # Use DuckDuckGo as the default search tool as requested
    logger.info("Using DuckDuckGo search tool as default")
    return DuckDuckGoSearchTool()

    # Commented out previous implementation that prioritized API-based search tools
    # if EnvironmentConfig.get_serper_api_key():
    #     logger.info("Using Serper search tool")
    #     return SerperSearchTool()
    # elif EnvironmentConfig.get_tavily_api_key():
    #     logger.info("Using Tavily search tool")
    #     return TavilySearchTool()
    # else:
    #     logger.warning("No search API keys found. Using DuckDuckGo as fallback.")
    #     return DuckDuckGoSearchTool()
