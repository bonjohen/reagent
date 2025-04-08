"""
Script to run a research query and see the results with the modified code.
"""

import asyncio
import json
from reagents.manager import ResearchManager

async def main():
    """Run a research query."""
    manager = ResearchManager()
    await manager.run("Graphene production")

    # Print the session ID for reference
    print(f"Research session ID: {manager._session_id}")

    # Load and print the JSON file
    if manager._session_id:
        try:
            with open(f"research_data/{manager._session_id}.json", "r") as f:
                data = json.load(f)
                print("\nReport Short Summary:")
                print(data["report"]["short_summary"])
                print("\nFollow-up Questions:")
                for i, question in enumerate(data["report"]["follow_up_questions"], 1):
                    print(f"{i}. {question}")
        except Exception as e:
            print(f"Error loading JSON file: {e}")

if __name__ == "__main__":
    asyncio.run(main())
