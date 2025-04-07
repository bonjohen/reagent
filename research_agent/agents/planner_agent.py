from pydantic import BaseModel, Field
import json
import re

from agents import Agent

# Define the model to use
PLANNER_MODEL = "gpt-3.5-turbo"  # Using GPT-3.5-turbo for compatibility

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
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common JSON formatting issues
                fixed_json_str = cls._attempt_json_repair(json_str)
                data = json.loads(fixed_json_str)

            # Validate required fields
            if 'searches' not in data:
                raise ValueError("Missing required field: 'searches'")

            # Validate that searches is a list
            if not isinstance(data['searches'], list):
                raise ValueError("'searches' must be a list")

            # Validate each search item
            for i, item in enumerate(data['searches']):
                if not isinstance(item, dict):
                    raise ValueError(f"Search item {i} must be an object")
                if 'query' not in item:
                    raise ValueError(f"Search item {i} missing required field: 'query'")
                if 'reason' not in item:
                    raise ValueError(f"Search item {i} missing required field: 'reason'")
                if not isinstance(item['query'], str):
                    raise ValueError(f"Search item {i}: 'query' must be a string")
                if not isinstance(item['reason'], str):
                    raise ValueError(f"Search item {i}: 'reason' must be a string")

            return cls.model_validate(data)
        except Exception as e:
            # Create a fallback plan if parsing fails
            fallback_data = {
                'searches': [
                    {
                        'query': 'error in search plan generation',
                        'reason': f"Error parsing search plan: {str(e)}"
                    },
                    {
                        'query': 'basic research methodology',
                        'reason': 'Fallback search to provide some useful information'
                    }
                ]
            }
            print(f"Error parsing search plan JSON: {str(e)}\nFalling back to basic search plan.")
            return cls.model_validate(fallback_data)

    @staticmethod
    def _attempt_json_repair(json_str: str) -> str:
        """Attempt to repair common JSON formatting issues."""
        # Replace single quotes with double quotes (common mistake)
        repaired = re.sub(r"'([^']*)'\s*:", r'"\1":', json_str)

        # Fix unquoted keys
        repaired = re.sub(r"([{,])\s*(\w+)\s*:", r'\1"\2":', repaired)

        # Fix trailing commas in arrays/objects
        repaired = re.sub(r',\s*([\]}])', r'\1', repaired)

        # Fix missing quotes around string values
        repaired = re.sub(r':\s*([^\s\d"\'{\[\]}][^,\]}]*)', r':"\1"', repaired)

        return repaired

# Create the planner agent with a valid model name
planner_agent = Agent(
    name="PlannerAgent",
    instructions=PROMPT,
    model=PLANNER_MODEL
)
