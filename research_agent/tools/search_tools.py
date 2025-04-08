"""
Custom search tools using Serper and Tavily APIs.
These provide more reliable search functionality than the default WebSearchTool.
"""

import os
import json
import aiohttp
import logging
from typing import Optional, Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SerperSearchTool:
    """Search tool that uses the Serper API to get Google search results."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Serper search tool.

        Args:
            api_key: Serper API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.environ.get("SERPER_API_KEY")
        self.endpoint = "https://google.serper.dev/search"

        # Validate API key format
        if self.api_key:
            self._validate_api_key()

    def _validate_api_key(self) -> None:
        """Validate the Serper API key format.

        Serper API keys are typically 32-character alphanumeric strings.
        """
        if not self.api_key:
            return

        # Check for minimum length
        if len(self.api_key) < 20:  # Serper keys are typically longer
            logger.warning(f"Serper API key appears to be too short: {len(self.api_key)} chars")

        # Check for valid characters (alphanumeric)
        if not self.api_key.isalnum():
            logger.warning("Serper API key contains non-alphanumeric characters")

    async def search(self, query: str, num_results: int = 5) -> str:
        """Perform a search using the Serper API.

        Args:
            query: The search query
            num_results: Number of results to return

        Returns:
            A string containing the search results
        """
        if not self.api_key:
            logger.warning("Serper API key not found. Search functionality will be limited.")
            return f"[Search for '{query}' failed: No Serper API key provided]"

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": num_results
        }

        try:
            logger.info(f"Performing Serper search for: {query}")
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Serper API error: {response.status} - {error_text}")
                        return f"[Search error: Serper API returned status {response.status}]"

                    data = await response.json()
                    return self._format_results(data, query)
        except Exception as e:
            logger.error(f"Error in Serper search: {str(e)}")
            return f"[Search error: {str(e)}]"

    def _format_results(self, data: Dict[str, Any], query: str, max_chars: int = 8000) -> str:
        """Format the search results into a readable string with size limits.

        Args:
            data: The JSON response from Serper API
            query: The original search query
            max_chars: Maximum number of characters in the formatted results

        Returns:
            A formatted string with search results, truncated if necessary
        """
        results = []
        total_length = 0
        truncated = False

        # Add organic results
        if "organic" in data:
            for item in data["organic"]:
                title = item.get("title", "No title")
                link = item.get("link", "")
                snippet = item.get("snippet", "No description available")

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

        # Add knowledge graph if available
        if "knowledgeGraph" in data and not truncated:
            kg = data["knowledgeGraph"]
            title = kg.get("title", "")
            description = kg.get("description", "")

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
        if "relatedSearches" in data and data["relatedSearches"] and not truncated:
            # Limit the number of related searches
            related_searches = data["relatedSearches"][:5]  # Maximum 5 related searches
            related = "Related searches: " + ", ".join(related_searches) + "\n"

            # Check if adding related searches would exceed the limit
            if total_length + len(related) <= max_chars:
                results.append(related)
                total_length += len(related)
            else:
                truncated = True

        # If no results found
        if not results:
            return f"No results found for query: {query}"

        # Combine all results
        result_text = f"Search results for '{query}':\n\n" + "\n".join(results)

        # Add truncation notice if needed
        if truncated:
            truncation_notice = "\n[Note: Search results were truncated due to size limits]"
            result_text += truncation_notice

        return result_text


class TavilySearchTool:
    """Search tool that uses the Tavily API for web search."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Tavily search tool.

        Args:
            api_key: Tavily API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        self.endpoint = "https://api.tavily.com/search"

        # Validate API key format
        if self.api_key:
            self._validate_api_key()

    def _validate_api_key(self) -> None:
        """Validate the Tavily API key format.

        Tavily API keys typically start with 'tvly-' followed by a long alphanumeric string.
        """
        if not self.api_key:
            return

        # Check for proper prefix
        if not self.api_key.startswith("tvly-"):
            logger.warning("Tavily API key does not start with 'tvly-' prefix")

        # Check for minimum length
        if len(self.api_key) < 20:  # Tavily keys are typically longer
            logger.warning(f"Tavily API key appears to be too short: {len(self.api_key)} chars")

        # Check for valid characters after prefix
        key_body = self.api_key[5:] if self.api_key.startswith("tvly-") else self.api_key
        if not key_body.isalnum():
            logger.warning("Tavily API key contains invalid characters")

    async def search(self, query: str, search_depth: str = "basic", max_results: int = 5) -> str:
        """Perform a search using the Tavily API.

        Args:
            query: The search query
            search_depth: Either "basic" or "advanced"
            max_results: Maximum number of results to return

        Returns:
            A string containing the search results
        """
        if not self.api_key:
            logger.warning("Tavily API key not found. Search functionality will be limited.")
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

        try:
            logger.info(f"Performing Tavily search for: {query}")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.endpoint, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Tavily API error: {response.status} - {error_text}")
                        return f"[Search error: Tavily API returned status {response.status}]"

                    data = await response.json()
                    return self._format_results(data, query)
        except Exception as e:
            logger.error(f"Error in Tavily search: {str(e)}")
            return f"[Search error: {str(e)}]"

    def _format_results(self, data: Dict[str, Any], query: str, max_chars: int = 8000) -> str:
        """Format the search results into a readable string with size limits.

        Args:
            data: The JSON response from Tavily API
            query: The original search query
            max_chars: Maximum number of characters in the formatted results

        Returns:
            A formatted string with search results, truncated if necessary
        """
        results = []
        total_length = 0
        truncated = False

        # Calculate the header length to reserve space
        header = f"Search results for '{query}':\n\n"
        truncation_notice = "\n[Note: Search results were truncated due to size limits]"
        reserved_space = len(header) + len(truncation_notice)
        effective_max_chars = max_chars - reserved_space

        # Add the answer if available
        if "answer" in data and data["answer"] and effective_max_chars > 0:
            answer = data["answer"]
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
            for item in data["results"]:
                title = item.get("title", "No title")
                url = item.get("url", "")
                content = item.get("content", "No content available")

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

        # Combine all results
        header = f"Search results for '{query}':\n\n"
        truncation_notice = "\n[Note: Search results were truncated due to size limits]"

        # Ensure the final result respects the max_chars limit
        if truncated:
            # Include the truncation notice
            result_text = header + "\n".join(results) + truncation_notice

            # If still too long, truncate more
            if len(result_text) > max_chars:
                available_space = max_chars - len(header) - len(truncation_notice)
                if available_space > 0:
                    joined_results = "\n".join(results)
                    result_text = header + joined_results[:available_space] + truncation_notice
                else:
                    # Extreme case: even the header + notice is too long
                    result_text = (header + truncation_notice)[:max_chars]
        else:
            # No truncation needed
            result_text = header + "\n".join(results)

            # Final check to ensure we don't exceed max_chars
            if len(result_text) > max_chars:
                truncated = True
                available_space = max_chars - len(header) - len(truncation_notice)
                if available_space > 0:
                    joined_results = "\n".join(results)
                    result_text = header + joined_results[:available_space] + truncation_notice
                else:
                    # Extreme case: even the header + notice is too long
                    result_text = (header + truncation_notice)[:max_chars]

        return result_text


# Factory function to get the appropriate search tool based on available API keys
def get_search_tool():
    """Get the best available search tool based on available API keys."""
    # Prioritize Serper over Tavily since we're having issues with Tavily
    if os.environ.get("SERPER_API_KEY"):
        logger.info("Using Serper search tool")
        return SerperSearchTool()
    elif os.environ.get("TAVILY_API_KEY"):
        logger.info("Using Tavily search tool")
        return TavilySearchTool()
    else:
        logger.warning("No search API keys found. Search functionality will be limited.")
        return None
