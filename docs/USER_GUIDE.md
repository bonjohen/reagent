# Research Agent User Guide

## Introduction

The Research Agent is a powerful tool designed to help you conduct comprehensive research on any topic. It uses a combination of AI agents to plan, search, and synthesize information into well-structured reports.

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- (Optional) Serper API key or Tavily API key for enhanced search capabilities

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/research-agent.git
   cd research-agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv_reagent
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv_reagent\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv_reagent/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   - Windows:
     ```bash
     setx OPENAI_API_KEY "your-api-key-here"
     setx SERPER_API_KEY "your-serper-api-key-here"  # Optional
     setx TAVILY_API_KEY "your-tavily-api-key-here"  # Optional
     ```
   - macOS/Linux:
     ```bash
     export OPENAI_API_KEY="your-api-key-here"
     export SERPER_API_KEY="your-serper-api-key-here"  # Optional
     export TAVILY_API_KEY="your-tavily-api-key-here"  # Optional
     ```

## Usage

### Interactive Mode (Default)

The Research Agent now runs in interactive mode by default:

```bash
python main.py
```

This will display a menu with the following options:

1. **Continue with last session (resume)**: Resume the most recently used research session
2. **List all research sessions**: View all available research sessions
3. **Start a new research session**: Begin a new research project
4. **Resume a specific session**: Select a specific session to resume
5. **Exit**: Quit the application

When starting a new session, you will be prompted to enter a research topic. Type your topic and press Enter to begin the research process.

After completing a research session, you'll return to the menu where you can continue working with the same session, start a new one, or explore previous sessions.

### Command Line Options

The Research Agent also supports several command line options for direct access to specific functions:

- `-n` or `--new`: Start a new research session
- `-r` or `--resume`: Resume a previous research session by ID
- `-l` or `--list`: List all research sessions

Examples:

```bash
# Start a new research session directly
python main.py -n

# List all research sessions
python main.py -l

# Resume a specific research session
python main.py -r 20230101123456_my_research_topic
```

Using these command-line options bypasses the interactive menu and performs the specified action directly.

### Research Process

The Research Agent follows a three-step process:

1. **Planning**: The Planner Agent analyzes your research topic and creates a plan of search queries to gather comprehensive information.

2. **Searching**: The Search Agent executes the search queries and collects relevant information from the web.

3. **Writing**: The Writer Agent synthesizes the search results into a well-structured report with a summary, main content, and follow-up questions.

### Viewing Results

After the research is complete, the results will be displayed in the terminal. The report includes:

- A short summary of the findings
- A comprehensive report in markdown format
- Follow-up questions for further research

All research sessions are saved automatically and can be resumed later.

## Advanced Features

### Using Enhanced Search

If you've provided a Serper API key or Tavily API key, the Research Agent will use these services for enhanced search capabilities. These services provide more relevant and comprehensive search results compared to the basic search functionality.

### Customizing the Research Process

You can customize the research process by modifying the configuration files:

- `reagents/config.py`: Contains configuration settings for models and other parameters
- `reagents/agents/*.py`: Contains the agent implementations that can be customized

## Troubleshooting

### Common Issues

#### API Key Issues

If you encounter errors related to API keys:

1. Ensure your API keys are set correctly in your environment variables
2. Check that your API keys are valid and have not expired
3. Verify that you have sufficient credits/quota for the API services

#### Search Errors

If you encounter search errors:

1. Check your internet connection
2. Verify that your search API keys (Serper or Tavily) are valid
3. Try using a different search provider by setting the appropriate API key

#### Report Generation Errors

If the report generation fails:

1. Check the error message for specific issues
2. Try simplifying your research topic
3. Resume the session and try again

### Getting Help

If you continue to experience issues, please:

1. Check the [GitHub Issues](https://github.com/yourusername/research-agent/issues) for similar problems and solutions
2. Create a new issue with detailed information about your problem

## Examples

### Example 1: Using Interactive Mode

```bash
python main.py
```

This will display the interactive menu. Choose option 3 to start a new research session.

When prompted, enter: "The impact of artificial intelligence on healthcare"

The Research Agent will:
1. Create a plan of search queries related to AI in healthcare
2. Execute these searches to gather information
3. Generate a comprehensive report on the topic

After the research is complete, you'll return to the menu where you can:
- Choose option 1 to continue working with this session
- Choose option 3 to start a new research session on a different topic
- Choose option 5 to exit the application

### Example 2: Continuing a Session

After completing a research session on AI in healthcare:

1. From the interactive menu, choose option 1 to continue with the last session
2. The application will automatically load the AI healthcare session
3. You can view the report again or conduct additional research based on the follow-up questions

### Example 3: Using Command Line Options

```bash
# First, list all research sessions
python main.py -l

# Then, resume a specific session
python main.py -r 20230101123456_ai_healthcare

# Or start a new session directly
python main.py -n
```

These commands bypass the interactive menu and perform the specified action directly.

## Best Practices

1. **Be specific**: The more specific your research topic, the more focused and useful the results will be.

2. **Use enhanced search**: If possible, provide a Serper API key or Tavily API key for better search results.

3. **Use interactive mode for related research**: The interactive mode makes it easy to conduct a series of related research sessions without restarting the application.

4. **Continue with last session**: Use option 1 in the interactive menu to quickly pick up where you left off with your most recent research.

5. **Save session IDs**: Keep track of your research session IDs for future reference, especially for important research topics.

6. **Review and iterate**: Use the follow-up questions to conduct additional research and deepen your understanding.

7. **Combine multiple sessions**: For complex topics, consider breaking down your research into multiple sessions and combining the results.

## Conclusion

The Research Agent is a powerful tool for conducting comprehensive research on any topic. By following this guide, you can leverage its capabilities to gather and synthesize information efficiently.

For more advanced usage and customization options, refer to the project's README and code documentation.
