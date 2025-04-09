import json
import os
import subprocess
import time
import glob
from pathlib import Path

from reagents.agents.writer_agent import ReportData


def test_create_and_validate_research_document():
    """Test that creates a research document JSON file using the actual codebase functionality."""
    # Ensure the research_data directory exists
    os.makedirs("research_data", exist_ok=True)

    # Get the current list of JSON files in the research_data directory
    existing_files = set(glob.glob("research_data/*.json"))

    # Create a unique test query with timestamp to avoid conflicts
    timestamp = time.strftime("%Y%m%d%H%M%S")
    test_query = f"Test research document {timestamp}"

    # Execute the main.py script with the test query as command line arguments
    print(f"Running main.py with query: {test_query}")
    result = subprocess.run(["python", "main.py"] + test_query.split(),
                           capture_output=True, text=True, timeout=300)

    # Print the output for debugging
    print(f"Command output:\n{result.stdout}")
    if result.stderr:
        print(f"Command errors:\n{result.stderr}")

    # Check that the command executed successfully
    assert result.returncode == 0, f"Command failed with return code {result.returncode}\n{result.stderr}"

    # Get the new files created in the research_data directory
    time.sleep(2)  # Give a little time for file system operations to complete
    current_files = set(glob.glob("research_data/*.json"))
    new_files = current_files - existing_files

    # There should be at least one new file
    assert len(new_files) > 0, "No new files were created in the research_data directory"

    # Find the file that matches our test query
    # First try to find files created after we started the test
    matching_files = list(new_files)

    # If we have multiple files, try to narrow it down by checking file contents
    if len(matching_files) > 1:
        filtered_files = []
        for file_path in matching_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "query" in data and test_query in data["query"]:
                        filtered_files.append(file_path)
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")

        if filtered_files:
            matching_files = filtered_files

    assert len(matching_files) > 0, "No new research document files were created"

    # Use the most recently created file if there are multiple matches
    file_path = max(matching_files, key=os.path.getctime)

    # Verify the file exists
    assert os.path.exists(file_path), f"File {file_path} was not created"
    print(f"Found research document file: {file_path}")

    # Load the file
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check that the file has the expected structure
    # The file should have a status field
    assert "status" in data, "Missing 'status' field"
    assert data["status"] in ["completed", "searched", "planned"], f"Unexpected status: '{data['status']}'"

    # Check the search_questions structure
    assert "search_questions" in data, "Missing 'search_questions' field"
    assert "questions" in data["search_questions"], "Missing 'questions' field in search_questions"
    assert isinstance(data["search_questions"]["questions"], list), "'questions' field should be a list"
    assert len(data["search_questions"]["questions"]) > 0, "'questions' list is empty"

    # Check that at least one question has search results
    has_results = False
    for question in data["search_questions"]["questions"]:
        if isinstance(question, dict) and "results" in question:
            has_results = True
            # Check that results have the expected structure
            assert isinstance(question["results"], list), "'results' field should be a list"
            if len(question["results"]) > 0:
                result = question["results"][0]
                assert "title" in result, "Missing 'title' field in result"
                assert "url" in result, "Missing 'url' field in result"
                assert "description" in result, "Missing 'description' field in result"
            break

    # At least one question should have results
    assert has_results, "No questions have search results"

    # Check search_plan structure
    if "search_plan" in data:
        search_plan_data = data["search_plan"]

        assert "topic" in search_plan_data, "Missing 'topic' field in search_plan"
        assert "searches" in search_plan_data, "Missing 'searches' field in search_plan"

        # Check that searches is a list of items
        searches = search_plan_data["searches"]
        assert isinstance(searches, list), "'searches' is not a list"

        # Check each search item
        for item in searches:
            assert "query" in item, "Missing 'query' field in search item"

            # Check search_tool if present
            if "search_tool" in item:
                assert isinstance(item["search_tool"], str), "'search_tool' is not a string"

            # Check urls if present
            if "urls" in item:
                assert isinstance(item["urls"], list), "'urls' is not a list"

            # Check result if present
            if "result" in item:
                assert isinstance(item["result"], str), "'result' is not a string"

    # Check if search_questions is present (optional)
    if "search_questions" in data:
        assert isinstance(data["search_questions"], dict), "'search_questions' is not a dictionary"
        assert "questions" in data["search_questions"], "Missing 'questions' field in search_questions"
        assert isinstance(data["search_questions"]["questions"], list), "'questions' is not a list"

    print(f"Successfully created and validated research document: {file_path}")
    print(f"Test file created at: {file_path}")


def test_report_data_structure():
    """Test that the ReportData class has the correct structure without markdown_report and follow_up_questions."""
    # Create a test report
    report_data = ReportData(
        short_summary="This is a test summary",
        model="test-model"
    )

    # Verify the report structure
    report_dict = report_data.model_dump()

    # Check that required fields are present
    assert "short_summary" in report_dict
    assert "model" in report_dict

    # Check that markdown_report is not present
    assert "markdown_report" not in report_dict

    # Check that follow_up_questions is not present
    assert "follow_up_questions" not in report_dict

    # Check the values
    assert report_dict["short_summary"] == "This is a test summary"
    assert report_dict["model"] == "test-model"
