#!/usr/bin/env python3
"""
DuckDuckGo Search Demo Script

This script demonstrates how to use DuckDuckGo for web searches without requiring an API key.
It accepts a search query as command line arguments and prints the search results to the screen.
If no search query is provided, the script will exit with an error message.

DuckDuckGo Search Features:
- No API key required
- Privacy-focused search engine
- No tracking of user searches
- Clean and straightforward results
- Access to web search results programmatically
- Supports various search operators (e.g., site:, filetype:)
- Can filter results by region and language
- Returns titles, URLs, and snippets of content
"""

import sys
import requests
from typing import Dict, Any
from urllib.parse import quote_plus


def ddg_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Perform a search using DuckDuckGo.

    Args:
        query (str): The search query string
        max_results (int): Maximum number of search results to return

    Returns:
        Dict[str, Any]: The search results as a dictionary containing:
            - html: The raw HTML response from DuckDuckGo
            - query: The original search query
    """
    # Construct the search URL
    encoded_query = quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

    # Set up headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Parameters are set up, ready to make the request

    try:
        # Make the request
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        response.raise_for_status()

        # Return the raw HTML and query
        return {
            "query": query,
            "html": response.text
        }
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return {"error": str(http_err), "status_code": response.status_code}
    except Exception as err:
        print(f"An error occurred: {err}")
        return {"error": str(err)}


def print_results(results: Dict[str, Any]) -> None:
    """
    Print the search results in a readable format.

    Args:
        results (Dict[str, Any]): The search results from DuckDuckGo
    """
    # Check if there was an error
    if "error" in results:
        print(f"Search failed: {results.get('error')}")
        return

    # Print the original query
    print(f"Search results for: '{results.get('query', 'Unknown query')}'")

    # Extract and display search results
    if "html" in results and results["html"]:
        html = results["html"]
        import re

        # Extract titles, URLs, and snippets
        title_matches = re.findall(r'<h2 class="result__title[^>]*>\s*<a[^>]*>(.*?)</a>', html)
        url_matches = re.findall(r'<h2 class="result__title[^>]*>\s*<a[^>]*href="([^"]+)"', html)
        snippet_matches = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html)

        # Get the number of results found
        num_results = len(title_matches)

        # Display the top results (show how many were found)
        print(f"Displaying top {min(5, num_results)} of {num_results} results:")
        for i in range(min(5, num_results)):
            title = re.sub(r'<.*?>', '', title_matches[i]).strip()
            url = url_matches[i] if i < len(url_matches) else "No URL"
            snippet = re.sub(r'<.*?>', '', snippet_matches[i]).strip() if i < len(snippet_matches) else "No snippet"

            print(f"\n{i+1}. {title}")
            print(f"   URL: {url}")
            print(f"   Snippet: {snippet}")
    else:
        print("No HTML content found.")


def main():
    """
    Main function to get the search string from command line arguments and execute the search.
    """
    # Check if a search query was provided
    if len(sys.argv) < 2:
        print("ERROR: No search query provided.")
        print("Usage: python ddg_demo.py <search query>")
        sys.exit(1)

    # Get the search query from command line arguments
    query = " ".join(sys.argv[1:])

    # Perform the search
    results = ddg_search(
        query=query,
        max_results=5  # Number of results to return (used for display purposes only)
    )

    # Print the results
    print_results(results)


if __name__ == "__main__":
    main()
