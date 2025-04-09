import asyncio
import os
import argparse
from typing import Optional

# Configure logging first to suppress unwanted messages
from reagents.logging_config import configure_logging
configure_logging()

# Import project modules
from reagents.manager import ResearchManager
from reagents.persistence import ResearchPersistence
from reagents.config import EnvironmentConfig

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

def display_menu(last_session_id: Optional[str] = None) -> str:
    """Display the main menu and get the user's choice.

    Args:
        last_session_id: The ID of the last session that was run, if any

    Returns:
        The user's menu choice
    """
    print("\n" + "=" * 50)
    print("Research Agent - Main Menu")
    print("=" * 50)

    if last_session_id:
        print(f"Last session: {last_session_id}")

    print("\nOptions:")
    print("  1. Continue with last session (resume)")
    print("  2. List all research sessions")
    print("  3. Start a new research session")
    print("  4. Resume a specific session")
    print("  5. Generate research questions only")
    print("  6. Exit")

    while True:
        choice = input("\nEnter your choice (1-6): ").strip()
        if choice in ["1", "2", "3", "4", "5", "6"]:
            return choice
        print("Invalid choice. Please enter a number between 1 and 6.")

async def generate_questions_only(topic: str) -> None:
    """Generate research questions for a topic without running the full research process.

    Args:
        topic: The research topic to generate questions for
    """
    try:
        # Validate input
        if not topic or topic.strip() == "":
            print("Error: Please provide a non-empty research topic.")
            return

        # Check for very short or likely invalid topics
        if len(topic.strip()) < 5:
            print("Error: Topic is too short. Please provide a more detailed research topic.")
            return

        # Check for topics that are just punctuation or special characters
        if all(not c.isalnum() for c in topic.strip()):
            print("Error: Topic must contain at least one letter or number.")
            return

        topic = topic.strip()

        # Create a research manager
        manager = ResearchManager()

        # Generate questions
        print(f"\nGenerating research questions for topic: {topic}\n")
        question_result = await manager._generate_questions(topic)

        # Display the results
        if question_result.questions:
            print(f"\nGenerated {len(question_result.questions)} research questions:\n")
            for i, question in enumerate(question_result.questions, 1):
                print(f"{i}. {question}")
        else:
            print("\nNo questions were generated. Please try a different topic.")

    except Exception as e:
        print(f"Error generating questions: {str(e)}")

async def run_research_session(session_id: Optional[str] = None, query: Optional[str] = None) -> Optional[str]:
    """Run a research session with the given session ID and query.

    Args:
        session_id: The ID of the session to resume, if any
        query: The research query to use for a new session

    Returns:
        The ID of the session that was run, or None if there was an error
    """
    try:
        # If we have a session ID but no query, get the query from the session data
        if session_id and not query:
            persistence = ResearchPersistence()
            session_data = persistence.get_session_data(session_id)

            if not session_data:
                print(f"Error: Session {session_id} not found.")
                return None

            query = session_data.get("query", "")
            print(f"Resuming research session: {session_id}")
            print(f"Original query: {query}")

            # Create and run the research manager with the existing session ID
            manager = ResearchManager(session_id=session_id)
            await manager.run(query)

            # Return the session ID that was used
            return manager.session_id

        # If we don't have a session ID, we need a query
        elif not session_id and not query:
            # Get a new query from the user
            query = input("What would you like to research? ")

            # Validate input
            if not query or query.strip() == "":
                print("Error: Please provide a non-empty research query.")
                return None

            # Check for very short or likely invalid queries
            if len(query.strip()) < 5:
                print("Error: Query is too short. Please provide a more detailed research query.")
                return None

            # Check for queries that are just punctuation or special characters
            if all(not c.isalnum() for c in query.strip()):
                print("Error: Query must contain at least one letter or number.")
                return None

            query = query.strip()

        # For new sessions, use the same approach as command-line mode
        # Create a ResearchManager
        manager = ResearchManager()

        # Create a persistence instance to generate a session ID
        persistence = ResearchPersistence()
        session_id = persistence._generate_session_id(query)

        # Set the session ID in the manager
        manager.session_id = session_id

        # Run the research process
        await manager.run(query)

        # Display the location of the generated file
        file_path = os.path.join("research_data", f"{session_id}.json")
        print("\n" + "=" * 80)
        print(f"RESEARCH DOCUMENT CREATED AT:\n{os.path.abspath(file_path)}")
        print("=" * 80)

        # Return the session ID that was used or created
        return manager.session_id
    except Exception as e:
        print(f"Error running research session: {str(e)}")
        return None

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
    parser.add_argument("-n", "--new", action="store_true", help="Start a new research session")
    parser.add_argument("-q", "--questions-only", action="store_true", help="Generate research questions only without executing the full research process")
    parser.add_argument("search_terms", nargs="*", help="Optional search terms for a new research session")
    args = parser.parse_args()

    print("Research Agent powered by OpenAI Agent SDK")
    print("------------------------------------------")

    # If search terms are provided, use them for a new research session
    if args.search_terms:
        search_query = " ".join(args.search_terms)
        print(f"Starting new research session with query: {search_query}")

        # Create a ResearchManager directly to get the session ID
        manager = ResearchManager()

        # Create a persistence instance to generate a session ID
        persistence = ResearchPersistence()
        session_id = persistence._generate_session_id(search_query)

        # Set the session ID in the manager
        manager.session_id = session_id

        # Run the research process
        await manager.run(search_query)

        # Display the location of the generated file
        file_path = os.path.join("research_data", f"{session_id}.json")
        print("\n" + "=" * 80)
        print(f"RESEARCH DOCUMENT CREATED AT:\n{os.path.abspath(file_path)}")
        print("=" * 80)
        return

    # If specific command line arguments are provided, run in non-interactive mode
    if args.list or args.resume or args.new or args.questions_only:
        # Handle listing sessions
        if args.list:
            list_sessions()
            return

        # Handle resuming a session
        if args.resume:
            await run_research_session(session_id=args.resume)
            return

        # Handle starting a new session
        if args.new:
            await run_research_session()
            return

        # Handle generating questions only
        if args.questions_only:
            topic = input("Enter a research topic: ").strip()
            await generate_questions_only(topic)
            return

    # Otherwise, run in interactive mode with a menu
    last_session_id = None

    while True:
        choice = display_menu(last_session_id)

        if choice == "1":  # Continue with last session
            if last_session_id:
                last_session_id = await run_research_session(session_id=last_session_id)
            else:
                print("No previous session to continue. Please start a new session.")

        elif choice == "2":  # List all sessions
            list_sessions()

        elif choice == "3":  # Start a new session
            last_session_id = await run_research_session()

        elif choice == "4":  # Resume a specific session
            list_sessions()  # Show available sessions
            session_id = input("\nEnter the session ID to resume: ").strip()
            if session_id:
                last_session_id = await run_research_session(session_id=session_id)
            else:
                print("No session ID provided.")

        elif choice == "5":  # Generate questions only
            topic = input("\nEnter a research topic: ").strip()
            if topic:
                await generate_questions_only(topic)
            else:
                print("No topic provided.")

        elif choice == "6":  # Exit
            print("\nExiting Research Agent. Goodbye!")
            break

if __name__ == "__main__":
    asyncio.run(main())
