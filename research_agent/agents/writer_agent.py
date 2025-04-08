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
            
            # Try to parse the JSON
            logger.debug(f"[{model}] Attempting to parse JSON with json.loads()")
            try:
                data = json.loads(json_str)
                logger.debug(f"[{model}] JSON parsed successfully")
            except json.JSONDecodeError as json_err:
                logger.debug(f"[{model}] JSON decode error: {str(json_err)}")
                logger.debug(f"[{model}] Error position: {json_err.pos}, line: {json_err.lineno}, column: {json_err.colno}")
                logger.debug(f"[{model}] JSON snippet at error: {json_str[max(0, json_err.pos-20):json_err.pos+20]}")
                
                # Try to fix common JSON formatting issues
                logger.debug(f"[{model}] Attempting to repair JSON")
                fixed_json_str = cls._attempt_json_repair(json_str)
                logger.debug(f"[{model}] Repaired JSON length: {len(fixed_json_str)}")
                logger.debug(f"[{model}] Repaired JSON preview: {fixed_json_str[:100]}..." if len(fixed_json_str) > 100 else f"[{model}] Repaired JSON: {fixed_json_str}")
                
                try:
                    data = json.loads(fixed_json_str)
                    logger.debug(f"[{model}] Repaired JSON parsed successfully")
                except json.JSONDecodeError as repair_err:
                    logger.debug(f"[{model}] Repair failed, JSON still invalid: {str(repair_err)}")
                    
                    # Try a more aggressive approach - convert the JSON to a proper format
                    logger.debug(f"[{model}] Attempting more aggressive JSON repair")
                    try:
                        # Extract the components manually using regex
                        short_summary_match = re.search(r'"short_summary"\s*:\s*"([^"]*)"', json_str)
                        
                        # Try two different patterns for markdown_report
                        # Pattern 1: markdown_report followed by follow_up_questions
                        markdown_report_match = re.search(r'"markdown_report"\s*:\s*"(.*?)"\s*,\s*"follow_up_questions"', json_str, re.DOTALL)
                        
                        # Pattern 2: markdown_report at the end of the JSON
                        if not markdown_report_match:
                            markdown_report_match = re.search(r'"markdown_report"\s*:\s*"(.*?)"\s*\}', json_str, re.DOTALL)
                        
                        follow_up_questions_match = re.search(r'"follow_up_questions"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                        
                        # If we have short_summary and markdown_report but not follow_up_questions,
                        # we can create default follow-up questions
                        if short_summary_match and markdown_report_match:
                            short_summary = short_summary_match.group(1)
                            markdown_report = markdown_report_match.group(1)
                            
                            # Clean up the markdown report - replace escaped newlines with actual newlines
                            markdown_report = markdown_report.replace('\\n', '\n')
                            
                            # Parse the follow-up questions if available, otherwise use defaults
                            follow_up_questions = []
                            if follow_up_questions_match:
                                follow_up_questions_str = follow_up_questions_match.group(1)
                                for q in re.findall(r'"([^"]*)"', follow_up_questions_str):
                                    follow_up_questions.append(q)
                            else:
                                # Default follow-up questions if none are found
                                follow_up_questions = [
                                    "What are the most recent developments in this field?",
                                    "How might these findings impact related industries?",
                                    "What ethical considerations should be taken into account?",
                                    "What are the limitations of the current research?",
                                    "What future research directions seem most promising?"
                                ]
                            
                            # Create a clean JSON object
                            data = {
                                "short_summary": short_summary,
                                "markdown_report": markdown_report,
                                "follow_up_questions": follow_up_questions
                            }
                            logger.debug(f"[{model}] Manual extraction successful")
                        else:
                            raise ValueError("Could not extract all required fields")
                    except Exception as e:
                        logger.debug(f"[{model}] Manual extraction failed: {str(e)}")
                        raise
            
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
                'markdown_report': f"# Error in Report Generation\n\nThere was an error parsing the report data: {str(e)}\n\nRaw response:\n\n```json\n{response}\n```",
                'follow_up_questions': ["What went wrong with the report generation?", "How can the report format be improved?"]
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
        """Attempt to repair common JSON formatting issues."""
        # First, check if the JSON is missing the follow_up_questions field
        if '"markdown_report"' in json_str and '"follow_up_questions"' not in json_str:
            # Add default follow_up_questions before the closing brace
            if json_str.rstrip().endswith('}'):
                json_str = json_str.rstrip()[:-1] + ',\n    "follow_up_questions": [\n        "What are the most recent developments in this field?",\n        "How might these findings impact related industries?",\n        "What ethical considerations should be taken into account?",\n        "What are the limitations of the current research?",\n        "What future research directions seem most promising?"\n    ]\n}'
        
        # First, normalize all newlines to \\n
        # Replace all actual newlines within string values with escaped newlines
        lines = json_str.split('\n')
        in_string = False
        processed_lines = []
        
        for line in lines:
            processed_line = ""
            i = 0
            while i < len(line):
                char = line[i]
                if char == '"' and (i == 0 or line[i-1] != '\\'):
                    in_string = not in_string
                processed_line += char
                i += 1
            
            if in_string:
                # If we're inside a string, add an escaped newline
                processed_lines.append(processed_line + "\\n")
            else:
                # If we're not inside a string, add a normal newline
                processed_lines.append(processed_line)
        
        # Rejoin without newlines (they're now escaped)
        repaired = ''.join(processed_lines)
        
        # Apply standard JSON repairs
        # Replace single quotes with double quotes (common mistake)
        repaired = re.sub(r"'([^']*)'\s*:", r'"\1":', repaired)

        # Fix unquoted keys
        repaired = re.sub(r"([{,])\s*(\w+)\s*:", r'\1"\2":', repaired)

        # Fix trailing commas in arrays/objects
        repaired = re.sub(r',\s*([\]}])', r'\1', repaired)

        # Fix missing quotes around string values
        repaired = re.sub(r':\s*([^\s\d"\'{\[\]}][^,\]}]*)', r':"\1"', repaired)

        # Remove control characters (ASCII control characters from 0-31 except tabs and newlines)
        repaired = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', repaired)
        
        return repaired

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
