"""
Repair script for fixing existing research session files with search result errors.

This utility script scans through all research session files and fixes any that contain
the "[Search error: sequence item 0: expected str instance, dict found]" error.

Usage:
    python -m utils.repair_session_files

This script is a maintenance tool and not part of the main application flow.
It should be run manually when corrupted session files are detected.
"""

import os
import json
import glob
from pathlib import Path

def repair_session_file(file_path):
    """
    Repair a single session file by fixing search result errors.
    
    Args:
        file_path: Path to the session file
        
    Returns:
        True if the file was modified, False otherwise
    """
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if the file has search results
        if 'search_results' not in data:
            print(f"  No search results in {file_path}")
            return False
        
        # Check if any search results contain the error
        search_results = data['search_results']
        modified = False
        
        if isinstance(search_results, list):
            # Check each search result
            for i, result in enumerate(search_results):
                if isinstance(result, str) and "expected str instance, dict found" in result:
                    # This is an error message we want to keep as is
                    print(f"  Found error message in search result {i+1}")
                    modified = True
                elif not isinstance(result, str):
                    # This is a non-string result that needs to be converted to a string
                    print(f"  Converting non-string result {i+1} to error message")
                    search_results[i] = f"[Search error: sequence item {i}: expected str instance, {type(result).__name__} found]"
                    modified = True
        else:
            # If search_results is not a list, convert it to a list with an error message
            print(f"  Converting non-list search_results to list with error message")
            data['search_results'] = [f"[Search error: expected list instance, {type(search_results).__name__} found]"]
            modified = True
        
        if modified:
            # Write the modified data back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"  Repaired {file_path}")
            return True
        else:
            print(f"  No errors found in {file_path}")
            return False
            
    except Exception as e:
        print(f"  Error repairing {file_path}: {str(e)}")
        return False

def main():
    """
    Main function to repair all session files.
    """
    # Get the path to the research_data directory
    research_data_dir = Path("research_data")
    
    # Check if the directory exists
    if not research_data_dir.exists():
        print(f"Research data directory not found: {research_data_dir}")
        return
    
    # Find all JSON files in the research_data directory
    session_files = list(research_data_dir.glob("*.json"))
    
    if not session_files:
        print("No session files found")
        return
    
    print(f"Found {len(session_files)} session files")
    
    # Repair each file
    repaired_count = 0
    for file_path in session_files:
        print(f"Processing {file_path}")
        if repair_session_file(file_path):
            repaired_count += 1
    
    print(f"Repaired {repaired_count} out of {len(session_files)} session files")

if __name__ == "__main__":
    main()
