"""
Writer agent for generating research reports.

LEGACY VERSION: This is a previous version of the writer agent that has been superseded
by writer_agent_consolidated.py. It is kept for reference purposes only.

This version includes updates to the report generation process, including better
JSON parsing and error handling.
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
            json_match = re.search(r'```(?:json)?\s*(.*?)```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response
            
            # Handle escaped characters in the JSON string
            json_str = json_str.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            
            # Try to parse the JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                # Try to fix common JSON formatting issues
                fixed_json_str = cls._attempt_json_repair(json_str)
                data = json.loads(fixed_json_str)
            
            # Validate required fields
            required_fields = ['short_summary', 'markdown_report', 'follow_up_questions']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add the model information
            data['model'] = model
            
            # All validations passed, create the object
            return cls.model_validate(data)
            
        except Exception as e:
            # Create a fallback report if parsing fails
            fallback_data = {
                'short_summary': f"Error parsing report: {str(e)}",
                'markdown_report': f"# Error in Report Generation\n\nThere was an error parsing the report data: {str(e)}\n\nRaw response:\n\n{response}",
                'follow_up_questions': ["What went wrong with the report generation?", "How can the report format be improved?"]
            }
            print(f"Error parsing report JSON: {str(e)}\nFalling back to error report.")
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
        
        return repaired

# Create the writer agent with a valid model name
writer_agent = Agent(
    name="WriterAgent",
    instructions=PROMPT,
    model=WRITER_MODEL
)
