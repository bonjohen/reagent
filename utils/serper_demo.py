#!/usr/bin/env python3
"""
Serper Search Demo Script

This script demonstrates how to use Serper.dev for web searches.
It accepts a search query as command line arguments and prints the search results to the screen.
If no search query is provided, the script will exit with an error message.

Serper Search Features:
- Requires an API key (set as SERPER_API_KEY environment variable)
- Provides access to Google search results via API
- Returns structured data including titles, URLs, and snippets
- Supports various search types (web, images, news, etc.)
- Offers clean and straightforward results
- Provides position data for search results
"""

import os
import sys
import json
import requests
from typing import Dict, Any, List, Optional

# API endpoint for Serper
SERPER_API_ENDPOINT = "https://google.serper.dev/search"

def serper_search(
    query: str,
    api_key: Optional[str] = None,
    max_results: int = 5,
    search_type: str = "search"  # Options: search, images, news, places
) -> Dict[str, Any]:
    """
    Perform a search using Serper.dev API.

    Args:
        query (str): The search query string
        api_key (str, optional): Serper API key. If not provided, will look for SERPER_API_KEY env var
        max_results (int): Maximum number of search results to return
        search_type (str): Type of search to perform (search, images, news, places)

    Returns:
        Dict[str, Any]: The search results as a dictionary
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("SERPER_API_KEY")
        if not api_key:
            raise ValueError("No Serper API key provided. Set SERPER_API_KEY environment variable or pass api_key parameter.")
    
    # Set up headers with API key
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    # Set up the payload
    payload = {
        "q": query,
        "num": max_results
    }
    
    # Print search parameters for debugging
    print("\nSerper Search Parameters:")
    print(f"  Query: {query}")
    print(f"  Max Results: {max_results}")
    print(f"  Search Type: {search_type}")
    print()
    
    try:
        # Make the request
        response = requests.post(SERPER_API_ENDPOINT, headers=headers, json=payload)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        results = response.json()
        
        return results
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if response.status_code == 400 and "Not enough credits" in response.text:
            print("Error: Your Serper account has run out of credits.")
        return {"error": str(http_err), "status_code": response.status_code, "response": response.text}
    except Exception as err:
        print(f"An error occurred: {err}")
        return {"error": str(err)}


def print_results(results: Dict[str, Any]) -> None:
    """
    Print the search results in a readable format.

    Args:
        results (Dict[str, Any]): The search results from Serper
    """
    # Check if there was an error
    if "error" in results:
        print(f"Search failed: {results.get('error')}")
        if "response" in results:
            print(f"Response: {results.get('response')}")
        return
    
    # Print the search information
    print(f"Search results:")
    print("=" * 80)
    
    # Print organic search results
    if "organic" in results:
        print("\nORGANIC RESULTS:")
        for i, result in enumerate(results["organic"], 1):
            print(f"\n{i}. {result.get('title', 'No title')}")
            print(f"   URL: {result.get('link', 'No URL')}")
            print(f"   Position: {result.get('position', 'Unknown')}")
            if "snippet" in result:
                print(f"   Snippet: {result['snippet']}")
    
    # Print knowledge graph if available
    if "knowledgeGraph" in results:
        kg = results["knowledgeGraph"]
        print("\nKNOWLEDGE GRAPH:")
        print(f"Title: {kg.get('title', 'No title')}")
        if "description" in kg:
            print(f"Description: {kg['description']}")
        if "attributes" in kg:
            print("Attributes:")
            for key, value in kg["attributes"].items():
                print(f"  {key}: {value}")
    
    # Print related searches if available
    if "relatedSearches" in results:
        print("\nRELATED SEARCHES:")
        for i, search in enumerate(results["relatedSearches"], 1):
            print(f"{i}. {search.get('query', '')}")


def main():
    """
    Main function to get the search string from command line arguments and execute the search.
    """
    # Check if a search query was provided
    if len(sys.argv) < 2:
        print("ERROR: No search query provided.")
        print("Usage: python serper_demo.py <search query>")
        sys.exit(1)
    
    # Get the search query from command line arguments
    query = " ".join(sys.argv[1:])
    
    # Check if API key is set
    if not os.environ.get("SERPER_API_KEY"):
        print("WARNING: SERPER_API_KEY environment variable is not set.")
        print("Please set it before running this script:")
        print("  On Windows: set SERPER_API_KEY=your_api_key")
        print("  On Linux/Mac: export SERPER_API_KEY=your_api_key")
        sys.exit(1)
    
    # Perform the search
    results = serper_search(
        query=query,
        max_results=5,
        search_type="search"
    )
    
    # Print the results
    print_results(results)


if __name__ == "__main__":
    main()
