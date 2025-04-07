"""
Writer agent for generating research reports.
"""

import re
import json
from typing import List, ClassVar, Optional
from pydantic import BaseModel, Field, model_validator

from agents import Agent

# Constants
WRITER_MODEL = "gpt-3.5-turbo"

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
            print(f"[DEBUG] [{model}] Response length: {len(response)}")
            
            json_match = re.search(r'```(?:json)?\s*(.*?)```', response, re.DOTALL)
            if json_match:
                print(f"[DEBUG] [{model}] Found ```json code block")
                json_str = json_match.group(1).strip()
                print(f"[DEBUG] [{model}] Extracted JSON from ```json block, length: {len(json_str)}")
            else:
                print(f"[DEBUG] [{model}] No ```json block found, using full response")
                json_str = response
            
            # Handle escaped characters in the JSON string
            print(f"[DEBUG] [{model}] Handling escaped characters in JSON string")
            json_str = json_str.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            print(f"[DEBUG] [{model}] After handling escapes, JSON length: {len(json_str)}")
            
            # Try to parse the JSON
            print(f"[DEBUG] [{model}] Attempting to parse JSON with json.loads()")
            try:
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
                    raise ValueError(f"Missing required field: {field}")
                print(f"[DEBUG] [{model}] Field '{field}' is present")
            
            # Validate field types
            print(f"[DEBUG] [{model}] Validating field types")
            if not isinstance(data['short_summary'], str):
                raise TypeError(f"short_summary must be a string, got {type(data['short_summary'])}")
            print(f"[DEBUG] [{model}] short_summary type: {type(data['short_summary'])}")
            
            if not isinstance(data['markdown_report'], str):
                raise TypeError(f"markdown_report must be a string, got {type(data['markdown_report'])}")
            print(f"[DEBUG] [{model}] markdown_report type: {type(data['markdown_report'])}")
            
            if not isinstance(data['follow_up_questions'], list):
                raise TypeError(f"follow_up_questions must be a list, got {type(data['follow_up_questions'])}")
            print(f"[DEBUG] [{model}] follow_up_questions type: {type(data['follow_up_questions'])}")
            
            # Validate follow_up_questions items
            print(f"[DEBUG] [{model}] Validating follow_up_questions items")
            for i, q in enumerate(data['follow_up_questions']):
                if not isinstance(q, str):
                    raise TypeError(f"follow_up_questions[{i}] must be a string, got {type(q)}")
            
            # Add the model information
            data['model'] = model
            
            # All validations passed, create the object
            print(f"[DEBUG] [{model}] All validations passed, creating ReportData object")
            result = cls.model_validate(data)
            print(f"[DEBUG] [{model}] ReportData object created successfully")
            return result
            
        except Exception as e:
            print(f"[DEBUG] [{model}] Error in ReportData.from_response: {type(e).__name__}")
            print(f"[DEBUG] [{model}] Error message: {str(e)}")
            
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

        # Remove control characters (ASCII control characters from 0-31 except tabs and newlines)
        repaired = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', repaired)

        # Escape newlines in string values
        repaired = re.sub(r'"([^"]*)"', lambda m: '"' + m.group(1).replace('\n', '\\n').replace('\r', '\\r') + '"', repaired)

        return repaired

# Create the writer agent with a valid model name
writer_agent = Agent(
    name="WriterAgent",
    instructions=PROMPT,
    model=WRITER_MODEL
)
