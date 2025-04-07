import traceback
from typing import Optional

def format_error(e: Exception, context: Optional[str] = None) -> str:
    """
    Format an exception with detailed information for better debugging.
    
    Args:
        e: The exception to format
        context: Optional context information about where the error occurred
        
    Returns:
        A formatted error message with traceback information
    """
    error_type = type(e).__name__
    error_msg = str(e)
    tb = traceback.format_exc()
    
    # Create a detailed error message
    if context:
        formatted_error = f"Error in {context}: {error_type}: {error_msg}"
    else:
        formatted_error = f"{error_type}: {error_msg}"
    
    # Add traceback for debugging
    print(f"\nDetailed error traceback:\n{tb}")
    
    return formatted_error
