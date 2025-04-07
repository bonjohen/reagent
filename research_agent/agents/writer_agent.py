# Agent used to synthesize a final report from the individual summaries.
from pydantic import BaseModel, Field
import json
import re

from agents import Agent

# Instructions for the writer agent
PROMPT = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research "
    "assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words. Include proper citations and references "
    "when possible. Organize the content with clear headings and subheadings.\n\n"
    "IMPORTANT: Your final response must be in the following JSON format:\n"
    "```json\n"
    "{\"short_summary\": \"A 2-3 sentence summary of findings\", "
    "\"markdown_report\": \"The full report in markdown format\", "
    "\"follow_up_questions\": [\"Question 1\", \"Question 2\", \"Question 3\"]}\n"
    "```\n"
    "Ensure your response can be parsed as valid JSON. The markdown_report field should contain the full report with proper markdown formatting."
)

class ReportData(BaseModel):
    """Data structure for the final research report."""

    short_summary: str = Field(
        description="A short 2-3 sentence summary of the findings."
    )

    markdown_report: str = Field(
        description="The final report in markdown format."
    )

    follow_up_questions: list[str] = Field(
        description="Suggested topics to research further."
    )

    @classmethod
    def from_response(cls, response: str) -> 'ReportData':
        """Parse a JSON response into a ReportData object."""
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

            # Handle escaped quotes and newlines in the markdown_report field
            json_str = re.sub(r'\\n', '\n', json_str)  # Replace \n with actual newlines

            # Parse the JSON
            data = json.loads(json_str)
            return cls.model_validate(data)
        except Exception as e:
            raise ValueError(f"Failed to parse response as JSON: {str(e)}\nResponse: {response}")

# Create the writer agent
writer_agent = Agent(
    name="WriterAgent",
    instructions=PROMPT,
    model="gpt-3.5-turbo",  # Using GPT-3.5-turbo for compatibility
)
