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

# Basic validation of API key format
if not api_key.startswith("sk-") or len(api_key) < 20:
    print("Warning: OPENAI_API_KEY appears to be in an invalid format.")
    print("API keys typically start with 'sk-' and are at least 20 characters long.")
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

        query = query.strip()

    # Create and run the research manager
    manager = ResearchManager(session_id=session_id)
    await manager.run(query)

if __name__ == "__main__":
    asyncio.run(main())
