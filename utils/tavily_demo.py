#!/usr/bin/env python3
"""
Tavily Search API Demo Script

This script demonstrates how to use the Tavily Search API to perform web searches.
It accepts a search query as command line arguments and prints the search results to the screen.
If no search query is provided, the script will exit with an error message.

Tavily API Features:
- Real-time web search with high-quality results
- Supports both basic and advanced search depths
- Can include answers summarizing the search results
- Allows filtering by including or excluding specific domains
- Supports maximum results parameter to control the number of results
- Returns structured data including titles, URLs, and content snippets
- Provides search context for each result
- API key authentication for secure access
"""

import os
import sys
import requests
from typing import Dict, Any, Optional, List


def tavily_search(
    query: str,
    api_key: str,
    search_depth: str = "basic",
    max_results: int = 5,
    include_answer: bool = True,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform a search using the Tavily Search API.

    Args:
        query (str): The search query string
        api_key (str): Tavily API key for authentication
        search_depth (str): Either "basic" (faster, less detailed) or "advanced" (more comprehensive)
        max_results (int): Maximum number of search results to return (1-10)
        include_answer (bool): Whether to include an AI-generated answer summarizing the results
        include_domains (List[str], optional): List of domains to specifically include in the search
        exclude_domains (List[str], optional): List of domains to exclude from the search results

    Returns:
        Dict[str, Any]: The search results as a dictionary containing:
            - results: List of search results with title, url, and content
            - answer: Summary of the search results (if include_answer is True)
            - query: The original search query
    """
    # Set up the API endpoint
    endpoint = "https://api.tavily.com/search"

    # Set up the headers with the API key
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    # Set up the request parameters
    params = {
        "query": query,
        "search_depth": search_depth,
        "max_results": max_results,
        "include_answer": include_answer,
    }

    # Add optional domain filters if provided
    if include_domains:
        params["include_domains"] = include_domains
    if exclude_domains:
        params["exclude_domains"] = exclude_domains

    # Print all parameters for debugging
    print("\nTavily API Parameters:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Query: {query}")
    print(f"  Search Depth: {search_depth}")
    print(f"  Max Results: {max_results}")
    print(f"  Include Answer: {include_answer}")
    print(f"  Include Domains: {include_domains}")
    print(f"  Exclude Domains: {exclude_domains}")
    print(f"  API Key: {api_key[:5]}...{api_key[-4:] if len(api_key) > 9 else ''}")
    print()

    try:
        # Make the API request
        response = requests.post(endpoint, headers=headers, json=params)

        # Check if the request was successful
        response.raise_for_status()

        # Parse and return the JSON response
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 401:
            print(f"ERROR: Authentication failed. Please check your Tavily API key.")
        elif response.status_code == 429:
            print(f"ERROR: Too many requests or out of credits. Your Tavily account has likely run out of credits or hit rate limits.")
        elif response.status_code == 400:
            print(f"ERROR: Bad request. {response.text}")
        else:
            print(f"HTTP error occurred: {http_err}")
        return {"error": str(http_err), "status_code": response.status_code}
    except Exception as err:
        print(f"An error occurred: {err}")
        return {"error": str(err)}


def print_results(results: Dict[str, Any]) -> None:
    """
    Print the search results in a readable format.

    Args:
        results (Dict[str, Any]): The search results from the Tavily API
    """
    # Check if there was an error
    if "error" in results:
        print(f"Search failed: {results.get('error')}")
        return

    # Print the original query
    print(f"\nSearch results for: '{results.get('query', 'Unknown query')}'")
    print("=" * 80)

    # Print the answer if available
    if "answer" in results and results["answer"]:
        print("\nSUMMARY:")
        print("-" * 80)
        print(results["answer"])
        print("-" * 80)

    # Print each search result
    if "results" in results and results["results"]:
        print("\nDETAILED RESULTS:")
        for i, result in enumerate(results["results"], 1):
            print(f"\n{i}. {result.get('title', 'No title')}")
            print(f"   URL: {result.get('url', 'No URL')}")
            print(f"   Content: {result.get('content', 'No content')[:200]}...")
    else:
        print("\nNo results found.")


def main():
    """
    Main function to get the search string from command line arguments and execute the search.
    """
    # Check if a search query was provided
    if len(sys.argv) < 2:
        print("ERROR: No search query provided.")
        print("Usage: python tavily_demo.py <search query>")
        sys.exit(1)

    # Get the search query from command line arguments
    query = " ".join(sys.argv[1:])

    # Get the API key from environment variables
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("ERROR: TAVILY_API_KEY environment variable not found.")
        print("Please set your Tavily API key as an environment variable:")
        print("  Windows (PowerShell): $env:TAVILY_API_KEY = 'your-api-key'")
        print("  Windows (Command Prompt): set TAVILY_API_KEY=your-api-key")
        print("  Linux/macOS: export TAVILY_API_KEY='your-api-key'")
        sys.exit(1)

    # Perform the search
    results = tavily_search(
        query=query,
        api_key=api_key,
        search_depth="basic",  # Can be changed to "advanced" for more comprehensive results
        max_results=5,         # Number of results to return (1-10)
        include_answer=True,   # Include an AI-generated answer summarizing the results
        include_domains=None,  # Optional list of domains to include
        exclude_domains=None   # Optional list of domains to exclude
    )

    # Print the results
    print_results(results)


if __name__ == "__main__":
    main()
