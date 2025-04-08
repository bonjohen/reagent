import asyncio
import os
import argparse
from typing import Optional

# Configure logging first to suppress unwanted messages
from research_agent.logging_config import configure_logging
configure_logging()

# Import project modules
from research_agent.manager import ResearchManager
from research_agent.persistence import ResearchPersistence
from research_agent.config import EnvironmentConfig

# Get API keys from the centralized config
openai_api_key = EnvironmentConfig.get_openai_api_key()
serper_api_key = EnvironmentConfig.get_serper_api_key()
tavily_api_key = EnvironmentConfig.get_tavily_api_key()

import openai

async def validate_openai_api_key(key: str) -> bool:
    """Validate an OpenAI API key by making a test API call.

    Args:
        key: The OpenAI API key to validate

    Returns:
        bool: True if the key is valid, False otherwise
    """
    try:
        # Create a client with the provided API key
        client = openai.OpenAI(api_key=key)

        # Make a simple API call to test the key
        # We use the models endpoint as it's lightweight
        client.models.list()  # We don't need the response, just checking if it works

        # If we get here, the key is valid
        return True
    except Exception as e:
        # Any exception means the key is invalid
        print(f"API key validation error: {str(e)}")
        return False

async def check_openai_api_key(openai_api_key: Optional[str]) -> bool:
    """Check if the OpenAI API key is valid and exit if invalid."""
    if not openai_api_key:
        print("\nError: OPENAI_API_KEY environment variable is not set.")
        print("\nTo use this application, you need to add the OPENAI_API_KEY to your system environment variables.")
        print("\nYou can do this by:")
        print("  1. Getting an API key from https://platform.openai.com/api-keys")
        print("  2. Setting it as an environment variable:")
        print("     - On Windows: setx OPENAI_API_KEY your-api-key-here")
        print("     - On macOS/Linux: export OPENAI_API_KEY=your-api-key-here")
        print("\nExiting now.\n")
        exit(1)

    # Validate the API key by making a test API call
    if not await validate_openai_api_key(openai_api_key):
        print("\nError: Invalid OpenAI API key.")
        print("\nTo use this application, you need a valid OpenAI API key:")
        print("  1. Get an API key from https://platform.openai.com/api-keys")
        print("  2. Set the OPENAI_API_KEY environment variable")
        print("\nExiting now.\n")
        exit(1)

    return True

# Main entry point
if __name__ == "__main__":
    # We'll check the API key in the main function
    pass

def list_sessions() -> None:
    """List all available research sessions."""
    persistence = ResearchPersistence()
    sessions = persistence.list_sessions()

    if not sessions:
        print("No research sessions found.")
        return

    print("\nAvailable research sessions:")
    print("-" * 80)
    print(f"{'Session ID':<30} {'Query':<30} {'Status':<10} {'Date':<20}")
    print("-" * 80)

    for session in sessions:
        print(f"{session['session_id']:<30} {session['query'][:30]:<30} {session['status']:<10} {session['timestamp'][:19]:<20}")

async def main() -> None:
    """Main entry point for the research agent application."""
    # Check if the OpenAI API key is valid
    await check_openai_api_key(openai_api_key)

    # Check for search API keys
    if serper_api_key:
        print(f"Serper API key found. Web search will use Serper.")
        # Set it in the environment for the search tools to use
        os.environ["SERPER_API_KEY"] = serper_api_key

    if tavily_api_key:
        print(f"Tavily API key found. Web search will use Tavily.")
        # Set it in the environment for the search tools to use
        os.environ["TAVILY_API_KEY"] = tavily_api_key

    if not serper_api_key and not tavily_api_key:
        print("Warning: No search API keys found. Web search functionality will be limited.")
        print("For better search results, set SERPER_API_KEY or TAVILY_API_KEY environment variables.")

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Research Agent powered by OpenAI Agent SDK")
    parser.add_argument("-r", "--resume", help="Resume a previous research session by ID")
    parser.add_argument("-l", "--list", action="store_true", help="List all research sessions")
    args = parser.parse_args()

    # Handle listing sessions
    if args.list:
        list_sessions()
        return

    print("Research Agent powered by OpenAI Agent SDK")
    print("------------------------------------------")

    # Handle resuming a session
    session_id = None
    query = ""

    if args.resume:
        session_id = args.resume
        persistence = ResearchPersistence()
        session_data = persistence.get_session_data(session_id)

        if not session_data:
            print(f"Error: Session {session_id} not found.")
            return

        query = session_data.get("query", "")
        print(f"Resuming research session: {session_id}")
        print(f"Original query: {query}")
    else:
        # Get a new query from the user
        query = input("What would you like to research? ")

        # Validate input
        if not query or query.strip() == "":
            print("Error: Please provide a non-empty research query.")
            return

        # Check for very short or likely invalid queries
        if len(query.strip()) < 5:
            print("Error: Query is too short. Please provide a more detailed research query.")
            return

        # Check for queries that are just punctuation or special characters
        if all(not c.isalnum() for c in query.strip()):
            print("Error: Query must contain at least one letter or number.")
            return

        query = query.strip()

    # Create and run the research manager
    manager = ResearchManager(session_id=session_id)
    await manager.run(query)

if __name__ == "__main__":
    asyncio.run(main())
