from pydantic import BaseModel, Field
import json
import re
from typing import Optional

from agents import Agent

# Import centralized configuration
from reagents.config import ModelConfig

def load_prompt_template() -> str:
    """Load the question generation prompt template from file.

    Returns:
        The prompt template as a string with modified JSON format instructions
    """
    try:
        with open("prompts/question_generation_prompt.txt", "r", encoding="utf-8") as f:
            prompt_content = f.read()

            # Modify the prompt to generate 40-50 questions
            prompt_content = prompt_content.replace("{min_questions}-{max_questions}", "40-50")

            # Replace the JSON format instructions to use searches format without reason field
            if "Format your response as a JSON array of questions" in prompt_content:
                prompt_content = prompt_content.replace(
                    "Format your response as a JSON array of questions. Each question should be clear, focused, and end with a question mark.",
                    "IMPORTANT: Your response must be in the following JSON format:"
                )

                # Replace the example format section
                start_idx = prompt_content.find("Example format:")
                end_idx = prompt_content.find("If you cannot format as JSON")
                if start_idx != -1 and end_idx != -1:
                    example_section = prompt_content[start_idx:end_idx]
                    new_example_section = (
                        "Example format:\n"
                        "```json\n"
                        "{\"searches\": [\n"
                        "  \"What is [topic] and how is it defined in different contexts?\",\n"
                        "  \"How has [topic] evolved historically?\",\n"
                        "  \"What are the current trends in [topic]?\"\n"
                        "]}\n"
                        "```\n\n"
                    )
                    prompt_content = prompt_content.replace(example_section, new_example_section)
            else:
                # If we can't find the format section, append our instructions
                json_format_instructions = (
                    "\n\nIMPORTANT: Your response must be in the following JSON format:\n"
                    "```json\n"
                    "{\n"
                    "  \"searches\": [\n"
                    "    \"What is [topic] and how is it defined in different contexts?\",\n"
                    "    \"How has [topic] evolved historically?\",\n"
                    "    \"What are the current trends in [topic]?\"\n"
                    "  ]\n"
                    "}\n"
                    "```\n\n"
                    "Ensure your response can be parsed as valid JSON."
                )
                prompt_content += json_format_instructions

            return prompt_content
    except FileNotFoundError:
        # If the file doesn't exist, return a default prompt
        return (
            "Generate 40-50 focused research questions about {topic}.\n\n"
            "IMPORTANT: Your response must be in the following JSON format:\n"
            "```json\n"
            "{\n"
            "  \"searches\": [\n"
            "    \"What is [topic] and how is it defined in different contexts?\",\n"
            "    \"How has [topic] evolved historically?\",\n"
            "    \"What are the current trends in [topic]?\"\n"
            "  ]\n"
            "}\n"
            "```\n\n"
            "Ensure your response can be parsed as valid JSON."
        )

# Load the planner prompt
PLANNER_PROMPT = load_prompt_template()

class WebSearchItem(BaseModel):
    """Represents a single search query and its results."""

    query: str = Field(
        description="The search question to use for the web search."
    )
    reason: Optional[str] = Field(
        None,
        description="The reason for this search query."
    )
    search_tool: Optional[str] = Field(
        None,
        description="The search tool used for this query."
    )
    urls: Optional[list[str]] = Field(
        None,
        description="The URLs returned by the search."
    )
    result: Optional[str] = Field(
        None,
        description="The search result text."
    )
    search_results: Optional[list[dict]] = Field(
        None,
        description="The detailed search results including title, URL, and description."
    )

class WebSearchPlan(BaseModel):
    """A plan containing multiple search queries."""

    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )

    @classmethod
    def from_response(cls, response: str) -> 'WebSearchPlan':
        """Parse a JSON response into a WebSearchPlan object.

        Args:
            response: The JSON response from the planner agent

        Returns:
            A WebSearchPlan object with search items
        """
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            response = json_match.group(1)

        try:
            # Try to parse the JSON response
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # If parsing fails, try to repair common JSON formatting issues
                repaired = cls._attempt_json_repair(response)
                data = json.loads(repaired)

            # Validate required fields
            if 'searches' not in data:
                raise ValueError("Missing required field: 'searches'")

            # Validate that searches is a list
            if not isinstance(data['searches'], list):
                raise ValueError("'searches' must be a list")

            # Convert the list of strings to a list of WebSearchItem objects
            search_items = []
            for i, item in enumerate(data['searches']):
                if isinstance(item, str):
                    # If the item is a string, create a WebSearchItem with just the query
                    search_items.append({"query": item})
                elif isinstance(item, dict) and 'query' in item:
                    # If the item is a dict with a query field, use it directly
                    # (this handles backward compatibility with the old format)
                    search_items.append({"query": item['query']})
                else:
                    raise ValueError(f"Search item {i} must be a string or an object with a 'query' field")

            # Create a new data object with the converted search items
            converted_data = {
                'searches': search_items
            }

            return cls.model_validate(converted_data)
        except Exception as e:
            # Create an empty fallback plan - we'll rely on the question generator instead
            fallback_data = {
                'searches': []
            }

            # Log the error but don't create fallback questions
            # We'll rely on the question_generator_agent.txt to provide questions

            print(f"Error parsing search plan JSON: {str(e)}\nReturning empty search plan and relying on question generator.")
            return cls.model_validate(fallback_data)

    @staticmethod
    def _attempt_json_repair(json_str: str) -> str:
        """Attempt to repair common JSON formatting issues."""
        # Replace single quotes with double quotes (common mistake)
        repaired = json_str.replace("'", '"')
        
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
    instructions=PLANNER_PROMPT,
    model=ModelConfig.get_planner_model()
)

# We no longer need a separate question planner agent
# The planner_agent now handles both search planning and question generation
