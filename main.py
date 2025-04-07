import asyncio
import os
import argparse

from dotenv import load_dotenv

from research_agent.manager import ResearchManager
from research_agent.persistence import ResearchPersistence

# Load environment variables from .env file
load_dotenv()

# Check if OpenAI API key is set and validate format
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY environment variable is not set.")
    print("Please set it in a .env file or in your environment.")
    exit(1)

# Enhanced validation of API key format
def is_valid_api_key(key: str) -> bool:
    """Validate the format of an OpenAI API key."""
    # Check basic format (starts with 'sk-' and has sufficient length)
    if not key.startswith("sk-") or len(key) < 40:
        return False

    # Check that it only contains valid characters
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    return all(c in valid_chars for c in key[3:])  # Skip the 'sk-' prefix

if not is_valid_api_key(api_key):
    print("Error: OPENAI_API_KEY appears to be in an invalid format.")
    print("API keys typically start with 'sk-' and are 51 characters long.")
    print("They contain only letters, numbers, hyphens, and underscores.")
    response = input("Do you want to continue anyway? (y/n): ")
    if response.lower() != 'y':
        exit(1)

def list_sessions():
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
