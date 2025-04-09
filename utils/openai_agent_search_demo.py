#!/usr/bin/env python3
"""
OpenAI Agent SDK Search Demo Script

This script demonstrates how to use the OpenAI Agent SDK for web searches.
It accepts a search query as command line arguments and prints the search results to the screen.
If no search query is provided, the script will exit with an error message.

OpenAI Agent SDK Search Features:
- Requires an OpenAI API key (set as OPENAI_API_KEY environment variable)
- Uses OpenAI's built-in WebSearchTool for searching the web
- Returns comprehensive search results with citations
- Provides natural language summaries of search results
- Supports follow-up questions and exploration
- Accesses up-to-date information from the web
"""

import os
import sys
from typing import Dict, Any, Optional

# Try to import the OpenAI Agent SDK
try:
    from openai import OpenAI
    from agents import Agent, WebSearchTool, Runner
except ImportError:
    print("ERROR: OpenAI Agent SDK is not installed.")
    print("Please install it using: pip install openai-agents")
    sys.exit(1)

async def openai_agent_search(
    query: str,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini", #"gpt-4o",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Perform a search using OpenAI Agent SDK's WebSearchTool.

    Args:
        query (str): The search query string
        api_key (str, optional): OpenAI API key. If not provided, will look for OPENAI_API_KEY env var
        model (str): The OpenAI model to use for the agent
        verbose (bool): Whether to print detailed information during the search

    Returns:
        Dict[str, Any]: The search results as a dictionary
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No OpenAI API key provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")

    # Print search parameters for debugging
    if verbose:
        print("\nOpenAI Agent Search Parameters:")
        print(f"  Query: {query}")
        print(f"  Model: {model}")
        print()

    try:
        # Initialize the OpenAI client with the API key
        # Note: The OpenAI client is automatically used by the Agent SDK
        OpenAI(api_key=api_key)

        # Create an agent with web search capability
        agent = Agent(
            name="Search Agent",
            instructions="You are a helpful search assistant that provides comprehensive answers with citations.",
            tools=[WebSearchTool()],
            model=model
        )

        # Run the agent with the search query
        result = await Runner.run(agent, f"Search for information about: {query}. Provide a comprehensive answer with citations to sources.")

        # Format the response into a structured result
        return {
            "query": query,
            "response": result.final_output,
            "model": model
        }
    except Exception as e:
        error_message = str(e)
        print(f"Error during OpenAI Agent search: {error_message}")
        return {
            "error": error_message,
            "query": query
        }

def print_results(results: Dict[str, Any]) -> None:
    """
    Print the search results in a readable format.

    Args:
        results (Dict[str, Any]): The search results from OpenAI Agent
    """
    # Check if there was an error
    if "error" in results:
        print(f"Search failed: {results.get('error')}")
        return

    # Print the original query
    print(f"\nSearch results for: '{results.get('query', 'Unknown query')}'")
    print("=" * 80)

    # Print the response
    if "response" in results:
        print("\nRESPONSE:")
        print(results["response"])
    else:
        print("\nNo response found.")

    # Print model information
    if "model" in results:
        print(f"\nModel used: {results['model']}")

async def main():
    """
    Main function to get the search string from command line arguments and execute the search.
    """
    # Check if a search query was provided
    if len(sys.argv) < 2:
        print("ERROR: No search query provided.")
        print("Usage: python openai_agent_search_demo.py <search query>")
        sys.exit(1)

    # Get the search query from command line arguments
    query = " ".join(sys.argv[1:])

    # Check if API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY environment variable is not set.")
        print("Please set it before running this script:")
        print("  On Windows: set OPENAI_API_KEY=your_api_key")
        print("  On Linux/Mac: export OPENAI_API_KEY=your_api_key")
        sys.exit(1)

    # Perform the search
    results = await openai_agent_search(
        query=query,
        verbose=True
    )

    # Print the results
    print_results(results)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
