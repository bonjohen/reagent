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

    def _format_results(self, data: Dict[str, Any], query: str) -> str:
        """Format the search results into a readable string.

        Args:
            data: The JSON response from Serper API
            query: The original search query

        Returns:
            A formatted string with search results
        """
        results = []

        # Add organic results
        if "organic" in data:
            for item in data["organic"]:
                title = item.get("title", "No title")
                link = item.get("link", "")
                snippet = item.get("snippet", "No description available")
                results.append(f"Title: {title}\nURL: {link}\nDescription: {snippet}\n")

        # Add knowledge graph if available
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            title = kg.get("title", "")
            description = kg.get("description", "")
            if title and description:
                results.append(f"Knowledge Graph: {title} - {description}\n")

        # If no results found
        if not results:
            return f"No results found for query: {query}"

        # Combine all results
        return f"Search results for '{query}':\n\n" + "\n".join(results)


class TavilySearchTool:
    """Search tool that uses the Tavily API for web search."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Tavily search tool.

        Args:
            api_key: Tavily API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        self.endpoint = "https://api.tavily.com/search"

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

    def _format_results(self, data: Dict[str, Any], query: str) -> str:
        """Format the search results into a readable string.

        Args:
            data: The JSON response from Tavily API
            query: The original search query

        Returns:
            A formatted string with search results
        """
        results = []

        # Add the answer if available
        if "answer" in data and data["answer"]:
            results.append(f"Summary: {data['answer']}\n")

        # Add search results
        if "results" in data:
            for item in data["results"]:
                title = item.get("title", "No title")
                url = item.get("url", "")
                content = item.get("content", "No content available")
                results.append(f"Title: {title}\nURL: {url}\nContent: {content}\n")

        # If no results found
        if not results:
            return f"No results found for query: {query}"

        # Combine all results
        return f"Search results for '{query}':\n\n" + "\n".join(results)


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
