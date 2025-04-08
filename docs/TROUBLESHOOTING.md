# Troubleshooting Guide

This guide provides solutions to common issues you might encounter when using the Research Agent.

## API Key Issues

### Issue: "OPENAI_API_KEY environment variable is not set"

**Solution:**
1. Set the OPENAI_API_KEY environment variable:
   - Windows: `setx OPENAI_API_KEY "your-api-key-here"`
   - macOS/Linux: `export OPENAI_API_KEY="your-api-key-here"`
2. Restart your terminal or command prompt
3. Verify the key is set: `echo %OPENAI_API_KEY%` (Windows) or `echo $OPENAI_API_KEY` (macOS/Linux)

### Issue: "Invalid OpenAI API key"

**Solution:**
1. Check that your API key is correct by logging into your OpenAI account
2. Ensure your API key has not expired
3. Verify you have sufficient credits in your OpenAI account
4. Try generating a new API key from the OpenAI dashboard

### Issue: "Search API key not found"

**Solution:**
1. Set the appropriate search API key:
   - For Serper: `setx SERPER_API_KEY "your-serper-api-key-here"` (Windows) or `export SERPER_API_KEY="your-serper-api-key-here"` (macOS/Linux)
   - For Tavily: `setx TAVILY_API_KEY "your-tavily-api-key-here"` (Windows) or `export TAVILY_API_KEY="your-tavily-api-key-here"` (macOS/Linux)
2. Restart your terminal or command prompt
3. Verify the key is set: `echo %SERPER_API_KEY%` (Windows) or `echo $SERPER_API_KEY` (macOS/Linux)

## Search Issues

### Issue: "Search error: No results found"

**Solution:**
1. Try rephrasing your search query to be more specific
2. Check your internet connection
3. Verify that your search API keys are valid
4. Try using a different search provider by setting the appropriate API key

### Issue: "Search error: Rate limit exceeded"

**Solution:**
1. Wait a few minutes before trying again
2. Check your API usage on the provider's dashboard
3. Consider upgrading your API plan if you frequently hit rate limits

### Issue: "Search error: sequence item 0: expected str instance, dict found"

**Solution:**
1. This is a known issue with certain search results
2. Run the repair script to fix corrupted session files:
   ```bash
   python -m utils.repair_session_files
   ```
3. Resume your research session after running the repair script

## Report Generation Issues

### Issue: "Error parsing report JSON"

**Solution:**
1. This is usually a temporary issue with the AI model's output
2. Try resuming the session and generating the report again
3. If the issue persists, try simplifying your research topic

### Issue: "Missing required field in report"

**Solution:**
1. The AI model may have generated an incomplete report
2. Resume the session and try again
3. If the issue persists, check the session file for corrupted data

## Installation and Dependency Issues

### Issue: "ModuleNotFoundError: No module named 'X'"

**Solution:**
1. Ensure you've installed all dependencies: `pip install -r requirements.txt`
2. Check that your virtual environment is activated
3. If the issue persists, try installing the specific missing package: `pip install X`

### Issue: "ImportError: cannot import name 'X' from 'Y'"

**Solution:**
1. This usually indicates a version mismatch in dependencies
2. Try reinstalling the package: `pip uninstall Y && pip install Y`
3. Check that you're using the correct version of Python (3.8+)

## Performance Issues

### Issue: "Research process is very slow"

**Solution:**
1. Check your internet connection
2. Consider using a more powerful model for the planner agent (edit `config.py`)
3. Reduce the number of search queries by making your research topic more specific
4. Use enhanced search providers (Serper or Tavily) for faster and more relevant results

### Issue: "Out of memory error"

**Solution:**
1. Close other applications to free up memory
2. Reduce the scope of your research topic
3. Break your research into multiple smaller sessions

## Interactive Mode and Session Management Issues

### Issue: "Menu options not responding"

**Solution:**
1. Make sure you're entering a number between 1 and 5
2. Check that your terminal supports interactive input
3. Try running with a specific command line option instead (e.g., `python main.py -n`)

### Issue: "Last session not showing up in interactive mode"

**Solution:**
1. The last session is only tracked within a single run of the application
2. If you exit and restart the application, you'll need to select "Resume a specific session"
3. Use `python main.py -l` to see all available sessions

### Issue: "Session not found"

**Solution:**
1. Check that you're using the correct session ID
2. List all available sessions: `python main.py -l`
3. Verify that the session file exists in the `research_data` directory

### Issue: "Cannot resume session"

**Solution:**
1. Check that the session file is not corrupted
2. Try running the repair script: `python -m utils.repair_session_files`
3. If the issue persists, you may need to start a new research session

## Advanced Troubleshooting

### Debugging Mode

To enable more detailed logging:

1. Edit `reagents/logging_config.py`
2. Change the logging level from `INFO` to `DEBUG`
3. Run your research session again to see more detailed logs

### Checking Session Files

If you suspect issues with your session files:

1. Navigate to the `research_data` directory
2. Open the session file (JSON format) in a text editor
3. Check for obvious issues like truncated content or malformed JSON
4. Use the repair script if needed: `python -m utils.repair_session_files`

### API Response Issues

If you're getting unexpected responses from the OpenAI API:

1. Check the OpenAI status page for any ongoing issues: https://status.openai.com/
2. Try using a different model by editing `config.py`
3. Verify that your API requests are properly formatted

## Getting Additional Help

If you continue to experience issues:

1. Check the [GitHub Issues](https://github.com/yourusername/research-agent/issues) for similar problems and solutions
2. Create a new issue with detailed information about your problem, including:
   - Error messages
   - Steps to reproduce
   - Your environment (OS, Python version, etc.)
   - Relevant logs
3. Contact the maintainers for additional support
