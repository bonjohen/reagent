"""Writer agent for generating research reports.

This is a consolidated version of the writer agent that combines the best features
from writer_agent_updated.py, writer_agent_fixed.py, and writer_agent_improved.py.
"""

import re
import json
import logging
from typing import List, ClassVar, Optional
from pydantic import BaseModel, Field, model_validator

from agents import Agent

# Set up logging
logger = logging.getLogger(__name__)

# Constants
WRITER_MODEL = "gpt-3.5-turbo"
FALLBACK_MODEL = "gpt-3.5-turbo-0125"  # Fallback model if primary is unavailable

# Prompt for the writer agent
PROMPT = """
You are a research report writer. Your task is to create a comprehensive, well-structured report based on the search results provided.

Follow these guidelines:
1. Analyze the search results thoroughly to extract key information
2. Organize the information into a coherent, logical structure
3. Write in a clear, professional style
4. Include proper citations or references to the sources
5. Format the report using markdown for readability
6. Be objective and balanced in your presentation of information
7. Focus on the most relevant and recent information
8. Identify any gaps or limitations in the available information

Your output should be in the following JSON format:
```json
{
    "short_summary": "A brief 1-2 sentence summary of the report",
    "markdown_report": "The full report in markdown format",
    "follow_up_questions": ["3-5 questions for further research"]
}
```

Make sure your JSON is properly formatted and valid.
"""

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
    def from_response(cls, response: str, model: str = WRITER_MODEL) -> 'ReportData':
        """Parse a JSON response into a ReportData object."""
        try:
            print(f"\n[DEBUG] [{model}] ReportData.from_response called with response type: {type(response)}")
            print(f"[DEBUG] [{model}] Response length: {len(response)}")

            # Extract JSON from the response if it's wrapped in markdown code blocks
            if '```json' in response and '```' in response:
                print(f"[DEBUG] [{model}] Found ```json code block")
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
                print(f"[DEBUG] [{model}] Extracted JSON from ```json block, length: {len(json_str)}")
            elif '```' in response:
                print(f"[DEBUG] [{model}] Found ``` code block")
                start = response.find('```') + 3
                end = response.find('```', start)
                json_str = response[start:end].strip()
                print(f"[DEBUG] [{model}] Extracted JSON from ``` block, length: {len(json_str)}")
            else:
                print(f"[DEBUG] [{model}] No code blocks found, using raw response")
                json_str = response.strip()
                print(f"[DEBUG] [{model}] Using raw response as JSON, length: {len(json_str)}")

            # Handle escaped quotes and newlines in the markdown_report field
            print(f"[DEBUG] [{model}] Handling escaped characters in JSON string")
            json_str = re.sub(r'\\n', '\n', json_str)  # Replace \n with actual newlines
            print(f"[DEBUG] [{model}] After handling escapes, JSON length: {len(json_str)}")

            # Parse the JSON
            try:
                print(f"[DEBUG] [{model}] Attempting to parse JSON with json.loads()")
                data = json.loads(json_str)
                print(f"[DEBUG] [{model}] JSON parsed successfully")
            except json.JSONDecodeError as json_err:
                print(f"[DEBUG] [{model}] JSON decode error: {str(json_err)}")
                print(f"[DEBUG] [{model}] Error position: {json_err.pos}, line: {json_err.lineno}, column: {json_err.colno}")
                print(f"[DEBUG] [{model}] JSON snippet at error: {json_str[max(0, json_err.pos-20):json_err.pos+20]}")

                # Try to fix common JSON formatting issues
                print(f"[DEBUG] [{model}] Attempting to repair JSON")
                fixed_json_str = cls._attempt_json_repair(json_str)
                print(f"[DEBUG] [{model}] Repaired JSON length: {len(fixed_json_str)}")
                print(f"[DEBUG] [{model}] Repaired JSON preview: {fixed_json_str[:100]}..." if len(fixed_json_str) > 100 else f"[DEBUG] [{model}] Repaired JSON: {fixed_json_str}")

                try:
                    data = json.loads(fixed_json_str)
                    print(f"[DEBUG] [{model}] Repaired JSON parsed successfully")
                except json.JSONDecodeError as repair_err:
                    print(f"[DEBUG] [{model}] Repair failed, JSON still invalid: {str(repair_err)}")
                    raise

            # Validate required fields
            print(f"[DEBUG] [{model}] Validating required fields")
            required_fields = ['short_summary', 'markdown_report', 'follow_up_questions']
            for field in required_fields:
                if field not in data:
                    print(f"[DEBUG] [{model}] Missing required field: {field}")
                    print(f"[DEBUG] [{model}] Available fields: {list(data.keys())}")
                    raise ValueError(f"Missing required field: {field}")
                else:
                    print(f"[DEBUG] [{model}] Field '{field}' is present")

            # Validate field types
            print(f"[DEBUG] [{model}] Validating field types")
            print(f"[DEBUG] [{model}] short_summary type: {type(data['short_summary'])}")
            if not isinstance(data['short_summary'], str):
                print(f"[DEBUG] [{model}] short_summary is not a string: {data['short_summary']}")
                raise ValueError("'short_summary' must be a string")

            print(f"[DEBUG] [{model}] markdown_report type: {type(data['markdown_report'])}")
            if not isinstance(data['markdown_report'], str):
                print(f"[DEBUG] [{model}] markdown_report is not a string: {data['markdown_report']}")
                raise ValueError("'markdown_report' must be a string")

            print(f"[DEBUG] [{model}] follow_up_questions type: {type(data['follow_up_questions'])}")
            if not isinstance(data['follow_up_questions'], list):
                print(f"[DEBUG] [{model}] follow_up_questions is not a list: {data['follow_up_questions']}")
                raise ValueError("'follow_up_questions' must be a list")

            # Ensure follow_up_questions contains only strings
            print(f"[DEBUG] [{model}] Validating follow_up_questions items")
            if not all(isinstance(q, str) for q in data['follow_up_questions']):
                non_string_items = [q for q in data['follow_up_questions'] if not isinstance(q, str)]
                print(f"[DEBUG] [{model}] Non-string items in follow_up_questions: {non_string_items}")
                raise ValueError("All items in 'follow_up_questions' must be strings")

            print(f"[DEBUG] [{model}] All validations passed, creating ReportData object")
            try:
                result = cls.model_validate(data)
                print(f"[DEBUG] [{model}] ReportData object created successfully")
                return result
            except Exception as e:
                print(f"[DEBUG] [{model}] Error in model_validate: {type(e).__name__}: {str(e)}")
                raise
        except Exception as e:
            # Detailed error logging
            print(f"\n[DEBUG] [{model}] Exception in from_response: {type(e).__name__}")
            print(f"[DEBUG] [{model}] Exception message: {str(e)}")

            # Print stack trace
            import traceback
            print(f"[DEBUG] [{model}] Stack trace:")
            traceback.print_exc()

            # Create a fallback report if parsing fails
            print(f"[DEBUG] [{model}] Creating fallback error report")
            fallback_data = {
                'short_summary': f"Error parsing report: {str(e)}",
                'markdown_report': f"# Error in Report Generation\n\nThere was an error parsing the report data: {str(e)}\n\nRaw response:\n\n{response}",
                'follow_up_questions': ["What went wrong with the report generation?", "How can the report format be improved?"]
            }
            print(f"[{model}] Error parsing report JSON: {str(e)}\nFalling back to error report.")

            try:
                result = cls.model_validate(fallback_data)
                print(f"[DEBUG] [{model}] Fallback report created successfully")
                return result
            except Exception as validate_err:
                print(f"[DEBUG] [{model}] Error creating fallback report: {type(validate_err).__name__}: {str(validate_err)}")
                raise

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

# Create the writer agent with a valid model name
writer_agent = Agent(
    name="WriterAgent",
    instructions=PROMPT,
    model=WRITER_MODEL
)
