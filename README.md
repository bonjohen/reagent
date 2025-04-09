# Research Agent

A Python-based research agent built using the OpenAI Agent SDK. This agent helps you conduct research on any topic by:

1. Planning a series of search queries
2. Executing those searches in parallel
3. Synthesizing the results into a comprehensive report

## Features

- Multi-agent architecture with specialized agents for question generation, planning, searching, and writing
- Research question generation to enhance research quality
- Parallel execution of search queries for faster results
- Rich terminal output with progress indicators
- Detailed markdown reports with follow-up questions
- OpenAI tracing integration for debugging and optimization

## Requirements

- Python 3.9+
- OpenAI API key
- Search API key (Serper or Tavily) for web search functionality

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd research-agent
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your API keys as system environment variables:

   **Important**: This application requires API keys to be set directly in your system environment variables. It does not use .env files.

   ```
   # On Windows
   setx OPENAI_API_KEY your-openai-api-key-here
   setx SERPER_API_KEY your-serper-api-key-here  # Optional, for web search
   setx TAVILY_API_KEY your-tavily-api-key-here  # Optional, for web search

   # On macOS/Linux
   export OPENAI_API_KEY=your-openai-api-key-here
   export SERPER_API_KEY=your-serper-api-key-here  # Optional, for web search
   export TAVILY_API_KEY=your-tavily-api-key-here  # Optional, for web search
   ```

   For more information on setting up the search APIs, see [SEARCH_SETUP.md](SEARCH_SETUP.md).

## Usage

### Interactive Mode (Default)

Run the research agent in interactive mode:

```
python main.py
```

This will display a menu with the following options:
1. Continue with last session (resume)
2. List all research sessions
3. Start a new research session
4. Resume a specific session
5. Generate research questions only
6. Exit

When starting a new session, you will be prompted to enter a research topic. The agent will then:
1. Generate research questions to explore different aspects of the topic
2. Plan the research by generating search queries
3. Execute those searches
4. Synthesize the results into a comprehensive report

After completing a session, you can continue working with the same session or start a new one.

### Command Line Options

You can also use command line arguments for specific operations:

```
# List all research sessions
python main.py -l

# Resume a specific session
python main.py -r SESSION_ID

# Start a new research session
python main.py -n

# Generate research questions only
python main.py -q
```

## Architecture

The research agent consists of four specialized agents:

1. **Question Generator Agent**: Generates diverse research questions to explore different aspects of the topic
2. **Planner Agent**: Creates a plan of search queries based on the research topic
3. **Search Agent**: Executes web searches and summarizes the results
4. **Writer Agent**: Synthesizes the search results into a comprehensive report

These agents are orchestrated by the `ResearchManager` class, which handles the flow of information between them.

## Project Structure

```
.
├── reagents/            # Main application code
│   ├── agents/           # Agent implementations
│   │   ├── question_generator_agent.py
│   │   ├── planner_agent.py
│   │   ├── search_agent.py
│   │   └── writer_agent.py             # Writer agent implementation
│   ├── tools/            # Custom tools used by agents
│   │   └── search_tools.py
│   ├── config.py         # Configuration settings and app initialization
│   ├── manager.py        # Research manager orchestrating the agents
│   ├── persistence.py    # Data persistence functionality
│   └── printer.py        # Terminal output formatting
├── legacy/              # Legacy code kept for reference
│   └── agents/          # Previous agent implementations
├── utils/               # Utility scripts
│   └── repair_session_files.py  # Tool for fixing corrupted session files
├── prompts/             # Prompt templates
│   ├── question_generation_prompt.txt
│   ├── planner_prompt.txt
│   ├── search_prompt.txt
│   └── writer_prompt.txt
├── tests/               # Test suite
├── main.py              # Application entry point
├── requirements.txt     # Project dependencies
└── README.md            # This file
```

### Notes on Special Directories

- **legacy/**: Contains previous versions of code that have been superseded by newer implementations but are kept for reference purposes.
- **utils/**: Contains standalone utility scripts that are not part of the main application flow but are useful for maintenance or debugging.

## License

MIT
