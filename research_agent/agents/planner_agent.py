from pydantic import BaseModel, Field
import json

from agents import Agent

# Instructions for the planner agent
PROMPT = (
    "You are a helpful research assistant. Given a query, come up with a set of web searches "
    "to perform to best answer the query. Output between 5 and 10 terms to query for. "
    "Make sure the search terms are diverse and cover different aspects of the query. "
    "For each search term, provide a clear reason why this search is important.\n\n"
    "IMPORTANT: Your response must be in the following JSON format:\n"
    "```json\n"
    "{\"searches\": [{\"query\": \"search term 1\", \"reason\": \"reason for search 1\"}, "
    "{\"query\": \"search term 2\", \"reason\": \"reason for search 2\"}]}\n"
    "```\n"
    "Ensure your response can be parsed as valid JSON."
)

class WebSearchItem(BaseModel):
    """Represents a single search query with its rationale."""

    reason: str = Field(
        description="Your reasoning for why this search is important to the query."
    )
    query: str = Field(
        description="The search term to use for the web search."
    )

class WebSearchPlan(BaseModel):
    """A plan containing multiple search queries."""

    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )

    @classmethod
    def from_response(cls, response: str) -> 'WebSearchPlan':
        """Parse a JSON response into a WebSearchPlan object."""
        try:
            # Extract JSON from the response if it's wrapped in markdown code blocks
            if '```json' in response and '```' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                json_str = response[start:end].strip()
            else:
                json_str = response.strip()

            # Parse the JSON
            data = json.loads(json_str)
            return cls.model_validate(data)
        except Exception as e:
            raise ValueError(f"Failed to parse response as JSON: {str(e)}\nResponse: {response}")

# Create the planner agent
planner_agent = Agent(
    name="PlannerAgent",
    instructions=PROMPT,
    model="gpt-3.5-turbo",  # Using GPT-3.5-turbo for compatibility
)
