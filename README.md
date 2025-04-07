# Research Agent

A Python-based research agent built using the OpenAI Agent SDK. This agent helps you conduct research on any topic by:

1. Planning a series of search queries
2. Executing those searches in parallel
3. Synthesizing the results into a comprehensive report

## Features

- Multi-agent architecture with specialized agents for planning, searching, and writing
- Parallel execution of search queries for faster results
- Rich terminal output with progress indicators
- Detailed markdown reports with follow-up questions
- OpenAI tracing integration for debugging and optimization

## Requirements

- Python 3.9+
- OpenAI API key

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

3. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Usage

Run the research agent:

```
python main.py
```

You will be prompted to enter a research topic. The agent will then:
1. Plan the research by generating search queries
2. Execute those searches
3. Synthesize the results into a comprehensive report

## Architecture

The research agent consists of three specialized agents:

1. **Planner Agent**: Creates a plan of search queries based on the research topic
2. **Search Agent**: Executes web searches and summarizes the results
3. **Writer Agent**: Synthesizes the search results into a comprehensive report

These agents are orchestrated by the `ResearchManager` class, which handles the flow of information between them.

## License

MIT
