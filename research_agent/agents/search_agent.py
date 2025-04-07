import logging
# Import standard libraries

from agents import Agent, WebSearchTool
from agents.model_settings import ModelSettings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Instructions for the search agent
INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succinctly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so it's vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary "
    "itself. Include key facts, figures, and data points when available.\n\n"
    "If you encounter any errors or no results are found, clearly state this in your response "
    "along with any details about what went wrong."
)

# Custom web search tool with error handling
class EnhancedWebSearchTool(WebSearchTool):
    """Enhanced web search tool with better error handling."""

    async def _run(self, query: str) -> str:
        """Run the web search with error handling."""
        try:
            logger.info(f"Performing web search for: {query}")
            result = await super()._run(query)
            if not result or result.strip() == "":
                logger.warning(f"Empty result for query: {query}")
                return "No results found for this query. Please try a different search term."
            return result
        except Exception as e:
            error_msg = f"Error performing web search: {str(e)}"
            logger.error(error_msg)
            return error_msg

# Create the search agent
search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[EnhancedWebSearchTool()],  # Using our enhanced web search tool
    model_settings=ModelSettings(tool_choice="required"),  # Always use the search tool
)
