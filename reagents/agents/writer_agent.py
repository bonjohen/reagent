"""Writer agent for generating research reports.

This is a consolidated version of the writer agent that combines the best features
from writer_agent_updated.py, writer_agent_fixed.py, and writer_agent_improved.py.
"""

import re
import json
import logging
from typing import Optional
from pydantic import BaseModel, Field

from agents import Agent
from reagents.config import ModelConfig

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

Your output MUST be in the following JSON format:
{
    "short_summary": "A brief 1-2 sentence summary of the report"
}

CRITICAL INSTRUCTIONS:
1. Your response must be a valid JSON object with the exact fields shown above
2. Do not include any text outside of the JSON object
3. Do not include any markdown code blocks, backticks, or other formatting around the JSON
4. The entire response should be a valid JSON object that can be parsed directly
5. Do not include any explanations or notes outside the JSON structure
6. Make sure all quotes and brackets are properly balanced

Example of correct response format:
{"short_summary":"This is a summary."}
"""

class ReportData(BaseModel):
    """Data model for research reports."""

    short_summary: str = Field(..., description="A brief summary of the report")
    model: Optional[str] = Field(None, description="The model used to generate the report")

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
            # Check if response is None or empty
            if response is None:
                logger.debug(f"[{model}] Response is None")
                raise ValueError("Response is None")

            if not response.strip():
                logger.debug(f"[{model}] Response is empty or whitespace")
                raise ValueError("Response is empty or whitespace")

            # Log response details
            logger.debug(f"[{model}] Response length: {len(response)}")
            logger.debug(f"[{model}] Response preview: {response[:200]}..." if len(response) > 200 else f"[{model}] Response: {response}")

            # First, check if the response is already a valid JSON object
            stripped_response = response.strip()
            if stripped_response.startswith('{') and stripped_response.endswith('}'):
                logger.debug(f"[{model}] Response appears to be a JSON object, trying direct parsing")
                try:
                    # Try to parse it directly
                    data = json.loads(stripped_response)
                    logger.debug(f"[{model}] Direct JSON parsing successful")

                    # Check if it has the required fields
                    if all(field in data for field in ["short_summary", "markdown_report", "follow_up_questions"]):
                        logger.debug(f"[{model}] JSON has all required fields")
                        data["model"] = model
                        return cls.model_validate(data)
                except json.JSONDecodeError:
                    logger.debug(f"[{model}] Direct JSON parsing failed, continuing with extraction")

            # Extract JSON from the response if it's wrapped in ```json blocks
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

            # Use the extraction method to parse the JSON
            logger.debug(f"[{model}] Extracting fields from JSON")
            data = cls._extract_json_fields(json_str, model)

            # If extraction failed, try to create a report from the raw content
            if data is None:
                logger.debug(f"[{model}] Field extraction failed, trying to create report from raw content")

                # Try to find a title in the content
                title_match = re.search(r'#\s*(.*?)\n', response)
                if title_match:
                    title = title_match.group(1).strip()
                    logger.debug(f"[{model}] Found title: {title}")
                else:
                    title = "Research Report"
                    logger.debug(f"[{model}] No title found, using default: {title}")

                # Create a short summary from the title
                short_summary = f"Report on {title}"

                # We don't need to check for markdown or create follow-up questions anymore
                logger.debug(f"[{model}] Skipping markdown and follow-up questions extraction")

                data = {
                    "short_summary": short_summary
                }
                logger.debug(f"[{model}] Created report from raw content")

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
                'short_summary': f"Error parsing report: {str(e)}"
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
        # We don't need to add follow_up_questions anymore
        # Just continue with the repair process

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
        logger.debug(f"[{model}] JSON string length: {len(json_str)}")
        logger.debug(f"[{model}] JSON string preview: {json_str[:200]}..." if len(json_str) > 200 else f"[{model}] JSON string: {json_str}")

        # Check if the string is empty or just whitespace
        if not json_str or not json_str.strip():
            logger.debug(f"[{model}] JSON string is empty or whitespace")
            return None

        # Check if the string looks like JSON (starts with { or [)
        stripped = json_str.strip()
        if not (stripped.startswith('{') or stripped.startswith('[')):
            logger.debug(f"[{model}] JSON string doesn't start with {{ or [, trying to find JSON in the text")
            # Try to find JSON-like content in the string
            json_start = json_str.find('{')
            if json_start == -1:
                logger.debug(f"[{model}] No {{ found in the string")
                # No JSON object found, try to extract fields directly
                pass
            else:
                # Try to find the matching closing brace
                brace_count = 0
                in_quotes = False
                escape_next = False
                json_end = -1

                for i in range(json_start, len(json_str)):
                    char = json_str[i]

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
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break

                if json_end != -1:
                    logger.debug(f"[{model}] Found potential JSON object from index {json_start} to {json_end}")
                    json_str = json_str[json_start:json_end]
                    logger.debug(f"[{model}] Extracted JSON: {json_str[:200]}..." if len(json_str) > 200 else f"[{model}] Extracted JSON: {json_str}")

        # Try standard JSON parsing first
        try:
            data = json.loads(json_str)
            logger.debug(f"[{model}] Standard JSON parsing successful")

            # Validate required fields
            if "short_summary" not in data:
                logger.debug(f"[{model}] Missing short_summary field in parsed JSON")
                data["short_summary"] = "Summary not provided"

            # Remove markdown_report if present
            if "markdown_report" in data:
                logger.debug(f"[{model}] Removing markdown_report field from parsed JSON")
                data.pop("markdown_report")

            # Remove follow_up_questions if present
            if "follow_up_questions" in data:
                logger.debug(f"[{model}] Removing follow_up_questions field from parsed JSON")
                data.pop("follow_up_questions")

            return data
        except json.JSONDecodeError as json_err:
            logger.debug(f"[{model}] JSON decode error: {str(json_err)}")
            logger.debug(f"[{model}] Error position: {json_err.pos}, line: {json_err.lineno}, column: {json_err.colno}")
            logger.debug(f"[{model}] JSON snippet at error: {json_str[max(0, json_err.pos-50):min(len(json_str), json_err.pos+50)]}")

            # Try to fix common JSON formatting issues
            logger.debug(f"[{model}] Attempting to repair JSON")
            fixed_json_str = cls._attempt_json_repair(json_str)

            try:
                data = json.loads(fixed_json_str)
                logger.debug(f"[{model}] Repaired JSON parsed successfully")

                # Validate required fields
                if "short_summary" not in data:
                    logger.debug(f"[{model}] Missing short_summary field in repaired JSON")
                    data["short_summary"] = "Summary not provided"

                # Remove markdown_report if present
                if "markdown_report" in data:
                    logger.debug(f"[{model}] Removing markdown_report field from repaired JSON")
                    data.pop("markdown_report")

                # Remove follow_up_questions if present
                if "follow_up_questions" in data:
                    logger.debug(f"[{model}] Removing follow_up_questions field from repaired JSON")
                    data.pop("follow_up_questions")

                return data
            except json.JSONDecodeError:
                logger.debug(f"[{model}] Repair failed, trying field-by-field extraction")

                # Extract fields one by one
                short_summary = cls._extract_json_field(json_str, "short_summary")
                logger.debug(f"[{model}] Extracted short_summary: {short_summary}")

                # If we couldn't extract any fields, try to create them from the content
                if short_summary is None:
                    logger.debug(f"[{model}] Could not extract any fields, trying to create them from content")

                    # Try to find a title in the content
                    title_match = re.search(r'#\s*(.*?)\n', json_str)
                    if title_match:
                        title = title_match.group(1).strip()
                        logger.debug(f"[{model}] Found title: {title}")
                    else:
                        title = "Research Report"
                        logger.debug(f"[{model}] No title found, using default: {title}")

                    # We don't need to extract markdown_report anymore
                    logger.debug(f"[{model}] Skipping markdown_report extraction")

                    # Create a short summary from the title
                    short_summary = f"Report on {title}"
                    logger.debug(f"[{model}] Created short_summary: {short_summary}")

                    return {
                        "short_summary": short_summary
                    }

                # No follow_up_questions needed

                # If we couldn't extract short_summary, create a default one
                if short_summary is None:
                    short_summary = "Research Report"
                    logger.debug(f"[{model}] Created default short_summary")

                # Check if we have the required field
                if short_summary is not None:
                    logger.debug(f"[{model}] Field-by-field extraction successful")
                    return {
                        "short_summary": short_summary
                    }
                else:
                    logger.debug(f"[{model}] Field-by-field extraction failed completely")
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
