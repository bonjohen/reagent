"""
Script to run a research query and see the results.
"""

import asyncio
from reagents.manager import ResearchManager

async def main():
    """Run a research query."""
    manager = ResearchManager()
    await manager.run("Graphene production")

if __name__ == "__main__":
    asyncio.run(main())
