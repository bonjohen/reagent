"""Writer agent for generating research reports.

This is a consolidated version of the writer agent that combines the best features
from writer_agent_updated.py, writer_agent_fixed.py, and writer_agent_improved.py.
"""

import re
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from agents import Agent
from research_agent.config import ModelConfig

# Set up logging
logger = logging.getLogger(__name__)

# Constants
WRITER_MODEL = ModelConfig.WRITER_MODEL
FALLBACK_MODEL = ModelConfig.WRITER_FALLBACK_MODEL

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
    """Data model for research reports."""

    short_summary: str = Field(..., description="A brief summary of the report")
    markdown_report: str = Field(..., description="The full report in markdown format")
    follow_up_questions: List[str] = Field(default_factory=list, description="Follow-up questions for further research")
    model: Optional[str] = Field(None, description="The model used to generate the report")

    @model_validator(mode='after')
    def validate_follow_up_questions(self) -> 'ReportData':
        """Ensure follow_up_questions is a list of strings."""
        if not isinstance(self.follow_up_questions, list):
            self.follow_up_questions = []
        return self

    @classmethod
    def from_response(cls, response: str, model: str = None) -> 'ReportData':
        """
        Parse a response string into a ReportData object.

        Args:
            response: The response string from the agent
            model: The model used to generate the response

        Returns:
            A ReportData object
        """
        try:
            # Extract JSON from the response if it's wrapped in ```json blocks
            logger.debug(f"[{model}] Response length: {len(response)}")

            json_match = re.search(r'```(?:json)?\s*(.*?)```', response, re.DOTALL)
            if json_match:
                logger.debug(f"[{model}] Found ```json code block")
                json_str = json_match.group(1).strip()
                logger.debug(f"[{model}] Extracted JSON from ```json block, length: {len(json_str)}")
            else:
                logger.debug(f"[{model}] No ```json block found, using full response")
                json_str = response

            # Handle escaped characters in the JSON string
            logger.debug(f"[{model}] Handling escaped characters in JSON string")
            json_str = json_str.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            logger.debug(f"[{model}] After handling escapes, JSON length: {len(json_str)}")

            # Use the new extraction method to parse the JSON
            logger.debug(f"[{model}] Extracting fields from JSON")
            data = cls._extract_json_fields(json_str, model)

            # If extraction failed, raise an error
            if data is None:
                raise ValueError("Failed to extract required fields from JSON")

            # Validate required fields
            logger.debug(f"[{model}] Validating required fields")
            required_fields = ['short_summary', 'markdown_report', 'follow_up_questions']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
                logger.debug(f"[{model}] Field '{field}' is present")

            # Validate field types
            logger.debug(f"[{model}] Validating field types")
            if not isinstance(data['short_summary'], str):
                raise TypeError(f"short_summary must be a string, got {type(data['short_summary'])}")
            logger.debug(f"[{model}] short_summary type: {type(data['short_summary'])}")

            if not isinstance(data['markdown_report'], str):
                raise TypeError(f"markdown_report must be a string, got {type(data['markdown_report'])}")
            logger.debug(f"[{model}] markdown_report type: {type(data['markdown_report'])}")

            if not isinstance(data['follow_up_questions'], list):
                raise TypeError(f"follow_up_questions must be a list, got {type(data['follow_up_questions'])}")
            logger.debug(f"[{model}] follow_up_questions type: {type(data['follow_up_questions'])}")

            # Validate follow_up_questions items
            logger.debug(f"[{model}] Validating follow_up_questions items")
            for i, q in enumerate(data['follow_up_questions']):
                if not isinstance(q, str):
                    raise TypeError(f"follow_up_questions[{i}] must be a string, got {type(q)}")

            # Add the model information
            data['model'] = model

            # All validations passed, create the object
            logger.debug(f"[{model}] All validations passed, creating ReportData object")
            result = cls.model_validate(data)
            logger.debug(f"[{model}] ReportData object created successfully")
            return result

        except Exception as e:
            logger.debug(f"[{model}] Error in ReportData.from_response: {type(e).__name__}")
            logger.debug(f"[{model}] Error message: {str(e)}")

            # Create a fallback report if parsing fails
            logger.debug(f"[{model}] Creating fallback error report")
            fallback_data = {
                'short_summary': f"Error parsing report: {str(e)}",
                'markdown_report': f"# Raw json:\n\n```json\n{json_str}\n```",
                'follow_up_questions': ["Would you like to try a more specific query?", "Would you like to try a different topic?", "Would you like to see the raw search results?"]
            }
            logger.warning(f"[{model}] Error parsing report JSON: {str(e)}\nFalling back to error report.")

            try:
                result = cls.model_validate(fallback_data)
                logger.debug(f"[{model}] Fallback report created successfully")
                return result
            except Exception as validate_err:
                logger.error(f"[{model}] Error creating fallback report: {type(validate_err).__name__}: {str(validate_err)}")
                raise

    @staticmethod
    def _attempt_json_repair(json_str: str) -> str:
        """Attempt to repair common JSON formatting issues.

        This method applies a series of transformations to fix common JSON formatting issues:
        1. Adds missing follow_up_questions field if needed
        2. Fixes quote issues (single vs double quotes)
        3. Fixes unquoted keys
        4. Removes trailing commas
        5. Adds quotes around unquoted string values
        6. Removes control characters

        Args:
            json_str: The JSON string to repair

        Returns:
            The repaired JSON string
        """
        # First, check if the JSON is missing the follow_up_questions field
        if '"markdown_report"' in json_str and '"follow_up_questions"' not in json_str:
            # Add default follow_up_questions before the closing brace
            if json_str.rstrip().endswith('}'):
                default_questions = ',\n    "follow_up_questions": [\n'
                default_questions += '        "What additional information would you like about this topic?",\n'
                default_questions += '        "Are there specific aspects of this topic you want to explore further?",\n'
                default_questions += '        "Would you like more details about any particular section?",\n'
                default_questions += '        "Are there related topics you would like to research?",\n'
                default_questions += '        "Do you have any questions about the information presented?"\n'
                default_questions += '    ]\n}'

                json_str = json_str.rstrip()[:-1] + default_questions

        # Apply a series of regex replacements to fix common issues
        # These are ordered from most specific to most general

        # 1. Replace single quotes with double quotes for keys
        repaired = re.sub(r"'([^']*)'\s*:", r'"\1":', json_str)

        # 2. Fix unquoted keys
        repaired = re.sub(r"([{,])\s*(\w+)\s*:", r'\1"\2":', repaired)

        # 3. Fix trailing commas in arrays/objects
        repaired = re.sub(r',\s*([\]}])', r'\1', repaired)

        # 4. Fix missing quotes around string values
        repaired = re.sub(r':\s*([^\s\d"\'{\[\]}][^,\]}]*)', r':"\1"', repaired)

        # 5. Remove control characters (ASCII control characters from 0-31 except tabs and newlines)
        repaired = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', repaired)

        # 6. Handle escaped newlines consistently
        repaired = repaired.replace('\\n', '\n').replace('\\r', '\n')

        # 7. Handle escaped quotes consistently
        repaired = repaired.replace('\\"', '"')

        return repaired

    @classmethod
    def _extract_json_field(cls, json_str, field_name):
        """Extract a field from a JSON string using a robust approach.

        Args:
            json_str: The JSON string to extract from
            field_name: The name of the field to extract

        Returns:
            The extracted field value, or None if not found
        """
        # Try to find the field using a regex pattern
        # First, try to match quoted string values
        pattern = fr'"{field_name}"\s*:\s*"(.*?)"(?:\s*,|\s*}})'
        match = re.search(pattern, json_str, re.DOTALL)
        if match:
            return match.group(1)

        # If that fails, try to match array values
        if field_name == "follow_up_questions":
            pattern = fr'"{field_name}"\s*:\s*\[(.*?)\]'
            match = re.search(pattern, json_str, re.DOTALL)
            if match:
                # Extract the array items
                array_content = match.group(1)
                # Parse the array items (assuming they're strings)
                items = []
                for item_match in re.finditer(r'"(.*?)"', array_content):
                    items.append(item_match.group(1))
                return items

        # If that fails, try to match any value (not just quoted strings)
        pattern = fr'"{field_name}"\s*:\s*(.*?)(?=\s*,\s*"[^"]+":|\s*}})'
        match = re.search(pattern, json_str, re.DOTALL)
        if match:
            value = match.group(1).strip()
            # If it's a quoted string, remove the quotes
            if value.startswith('"') and value.endswith('"'):
                return value[1:-1]
            return value

        # If all else fails, try a manual extraction approach
        field_start_pos = json_str.find(f'"{field_name}"')
        if field_start_pos != -1:
            # Find the position of the first colon after the field name
            colon_pos = json_str.find(':', field_start_pos)
            if colon_pos != -1:
                # Find the position of the first non-whitespace character after the colon
                content_start = colon_pos + 1
                while content_start < len(json_str) and json_str[content_start].isspace():
                    content_start += 1

                # Special handling for arrays
                if field_name == "follow_up_questions" and content_start < len(json_str) and json_str[content_start] == '[':
                    # Find the matching closing bracket
                    bracket_count = 1
                    content_start += 1  # Skip the opening bracket
                    content_end = content_start
                    in_quotes = False
                    escape_next = False

                    while content_end < len(json_str) and bracket_count > 0:
                        char = json_str[content_end]

                        if escape_next:
                            escape_next = False
                        elif char == '\\':
                            escape_next = True
                        elif char == '"' and not escape_next:
                            in_quotes = not in_quotes
                        elif not in_quotes:
                            if char == '[':
                                bracket_count += 1
                            elif char == ']':
                                bracket_count -= 1

                        content_end += 1

                    if bracket_count == 0:  # Found the matching closing bracket
                        array_content = json_str[content_start:content_end-1].strip()  # -1 to exclude the closing bracket
                        # Parse the array items (assuming they're strings)
                        items = []
                        for item_match in re.finditer(r'"(.*?)"', array_content):
                            items.append(item_match.group(1))
                        return items
                else:
                    # For non-array fields, find the end of the field
                    content_end = content_start
                    brace_count = 0
                    in_quotes = False
                    escape_next = False

                    while content_end < len(json_str):
                        char = json_str[content_end]

                        if escape_next:
                            escape_next = False
                        elif char == '\\':
                            escape_next = True
                        elif char == '"' and not escape_next:
                            in_quotes = not in_quotes
                        elif not in_quotes:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                if brace_count > 0:
                                    brace_count -= 1
                                else:
                                    # End of the JSON object
                                    break
                            elif char == ',' and brace_count == 0:
                                # Found a comma at the top level, which indicates the end of this field
                                break

                        content_end += 1

                    # Extract the content
                    content = json_str[content_start:content_end].strip()

                    # If the content is a quoted string, remove the quotes
                    if content.startswith('"') and content.endswith('"'):
                        content = content[1:-1]

                    return content

        # Field not found
        return None

    @classmethod
    def _extract_json_fields(cls, json_str, model):
        """Extract all required fields from a JSON string.

        Args:
            json_str: The JSON string to extract from
            model: The model name for logging purposes

        Returns:
            A dictionary containing the extracted fields, or None if extraction failed
        """
        logger.debug(f"[{model}] Extracting fields from JSON string")

        # Try standard JSON parsing first
        try:
            data = json.loads(json_str)
            logger.debug(f"[{model}] Standard JSON parsing successful")
            return data
        except json.JSONDecodeError as json_err:
            logger.debug(f"[{model}] JSON decode error: {str(json_err)}")

            # Try to fix common JSON formatting issues
            logger.debug(f"[{model}] Attempting to repair JSON")
            fixed_json_str = cls._attempt_json_repair(json_str)

            try:
                data = json.loads(fixed_json_str)
                logger.debug(f"[{model}] Repaired JSON parsed successfully")
                return data
            except json.JSONDecodeError:
                logger.debug(f"[{model}] Repair failed, trying field-by-field extraction")

                # Extract fields one by one
                short_summary = cls._extract_json_field(json_str, "short_summary")
                logger.debug(f"[{model}] Extracted short_summary: {short_summary}")
                markdown_report = cls._extract_json_field(json_str, "markdown_report")
                logger.debug(f"[{model}] Extracted markdown_report: {markdown_report}")
                follow_up_questions = cls._extract_json_field(json_str, "follow_up_questions")

                # If we couldn't extract follow_up_questions, use default ones
                if follow_up_questions is None and short_summary is not None and markdown_report is not None:
                    follow_up_questions = [
                        "What additional information would you like about this topic?",
                        "Are there specific aspects of this topic you want to explore further?",
                        "Would you like more details about any particular section?",
                        "Are there related topics you would like to research?",
                        "Do you have any questions about the information presented?"
                    ]

                # Check if we extracted all required fields
                if short_summary is not None and markdown_report is not None and follow_up_questions is not None:
                    logger.debug(f"[{model}] Field-by-field extraction successful")
                    return {
                        "short_summary": short_summary,
                        "markdown_report": markdown_report,
                        "follow_up_questions": follow_up_questions
                    }
                else:
                    logger.debug(f"[{model}] Field-by-field extraction failed")
                    return None

# Create the writer agent with a valid model name
try:
    writer_agent = Agent(
        name="WriterAgent",
        instructions=PROMPT,
        model=WRITER_MODEL
    )
except Exception as e:
    logger.warning(f"Failed to initialize writer agent with model {WRITER_MODEL}: {str(e)}")
    logger.info(f"Falling back to model {FALLBACK_MODEL}")
    writer_agent = Agent(
        name="WriterAgent",
        instructions=PROMPT,
        model=FALLBACK_MODEL
    )
