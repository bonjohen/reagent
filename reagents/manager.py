from __future__ import annotations

import asyncio
import time
import traceback
from typing import Optional, List

from rich.console import Console

from agents import Runner, custom_span, gen_trace_id, trace

from reagents.agents.planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from reagents.agents.search_agent import search_agent
from reagents.agents.writer_agent import ReportData, writer_agent
from reagents.agents.question_generator_agent import generate_questions, QuestionGeneratorResult
from reagents.config import QuestionGeneratorConfig, ModelConfig
from reagents.printer import Printer
from reagents.error_utils import format_error
from reagents.persistence import ResearchPersistence

# Import custom search tools
try:
    from reagents.tools.search_tools import get_search_tool
    custom_search_tool = get_search_tool()
    print(f"Using custom search tool: {custom_search_tool.__class__.__name__ if custom_search_tool else 'None'}")
except ImportError:
    print("Custom search tools not available, falling back to default search")
    custom_search_tool = None

class ResearchManager:
    """
    Manages the research process by coordinating multiple agents:
    1. Planner agent: Creates a plan of search queries
    2. Search agent: Executes searches and summarizes results
    3. Writer agent: Synthesizes search results into a report
    """

    def __init__(self, session_id: Optional[str] = None):
        self.console = Console()
        self.printer = Printer(self.console)
        self.persistence = ResearchPersistence()
        self._session_id = session_id

    @property
    def session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self._session_id

    @session_id.setter
    def session_id(self, value: Optional[str]) -> None:
        """Set the session ID."""
        self._session_id = value

    async def run(self, query: str) -> None:
        """
        Run the research process for the given query.

        Args:
            query: The research query to investigate
        """
        # Generate a trace ID for tracking the research process
        trace_id = gen_trace_id()

        # Use the printer as a context manager to ensure cleanup
        with self.printer, trace("Research trace", trace_id=trace_id):
            try:
                self.printer.update_item(
                    "trace_id",
                    f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}",
                    is_done=True,
                    hide_checkmark=True,
                )

                # No demo mode

                self.printer.update_item(
                    "starting",
                    "Starting research...",
                    is_done=True,
                    hide_checkmark=True,
                )

                # Step 1: Generate research questions
                search_questions = None
                try:
                    # Check if we're resuming from a previous session with questions
                    if self._session_id:
                        session_data = self.persistence.get_session_data(self._session_id)
                        if session_data and "search_questions" in session_data:
                            # Restore questions from saved session
                            search_questions = session_data["search_questions"]
                            self.printer.update_item(
                                "generating_questions",
                                f"Restored {len(search_questions['questions'])} research questions from previous session",
                                is_done=True,
                            )

                    # If no questions were restored, generate new ones
                    if not search_questions:
                        question_result = await self._generate_questions(query)
                        search_questions = question_result.to_dict()

                        # Save the questions if we have a session ID
                        if self._session_id:
                            session_data = self.persistence.get_session_data(self._session_id) or {}
                            session_data["search_questions"] = search_questions
                            self.persistence.save_session_data(self._session_id, session_data)
                except Exception as e:
                    # Log the error but continue with the research process
                    error_msg = format_error(e, "question generation")
                    self.printer.update_item(
                        "warning",
                        f"Error generating questions: {error_msg}",
                        is_done=True,
                    )

                # Step 2: Plan the searches
                try:
                    # Check if we're resuming from a previous session
                    if self._session_id:
                        session_data = self.persistence.get_session_data(self._session_id)
                        if session_data and session_data.get("status") in ["planned", "searched"]:
                            self.printer.update_item(
                                "resuming",
                                f"Resuming research from previous session {self._session_id}",
                                is_done=True,
                            )

                            # Restore search plan from saved session
                            if "search_plan" in session_data:
                                search_plan_dict = session_data["search_plan"]
                                search_plan = WebSearchPlan.model_validate(search_plan_dict)
                                self.printer.update_item(
                                    "planning",
                                    f"Restored search plan with {len(search_plan.searches)} searches",
                                    is_done=True,
                                )
                            else:
                                # Create a new search plan
                                search_plan = await self._plan_searches(query)

                                # Merge questions from search_questions into search_plan if available
                                if search_questions and "questions" in search_questions and search_questions["questions"]:
                                    search_plan = self._merge_questions_into_search_plan(search_plan, search_questions)

                                    # Update the session data with the merged questions count
                                    if self._session_id:
                                        session_data = self.persistence.get_session_data(self._session_id) or {}
                                        if "search_questions" in session_data:
                                            session_data["search_questions"]["count"] = len(session_data["search_questions"]["questions"])
                                            self.persistence.save_session_data(self._session_id, session_data)
                        else:
                            # Invalid session, create a new search plan
                            search_plan = await self._plan_searches(query)

                            # Merge questions from search_questions into search_plan if available
                            if search_questions and "questions" in search_questions and search_questions["questions"]:
                                search_plan = self._merge_questions_into_search_plan(search_plan, search_questions)

                                # Update the session data with the merged questions count
                                if self._session_id:
                                    session_data = self.persistence.get_session_data(self._session_id) or {}
                                    if "search_questions" in session_data:
                                        session_data["search_questions"]["count"] = len(session_data["search_questions"]["questions"])
                                        self.persistence.save_session_data(self._session_id, session_data)
                    else:
                        # No session ID provided, create a new search plan
                        search_plan = await self._plan_searches(query)

                        # Merge questions from search_questions into search_plan if available
                        if search_questions and "questions" in search_questions and search_questions["questions"]:
                            search_plan = self._merge_questions_into_search_plan(search_plan, search_questions)

                            # Update the session data with the merged questions count
                            if self._session_id:
                                session_data = self.persistence.get_session_data(self._session_id) or {}
                                if "search_questions" in session_data:
                                    session_data["search_questions"]["count"] = len(session_data["search_questions"]["questions"])
                                    self.persistence.save_session_data(self._session_id, session_data)

                        # Save the search plan and get a new session ID
                        self._session_id = self.persistence.save_search_plan(
                            query,
                            search_plan.model_dump()
                        )
                        self.printer.update_item(
                            "session",
                            f"Created new research session: {self._session_id}",
                            is_done=True,
                        )
                except Exception as e:
                    # Sanitize error message to avoid exposing sensitive information
                    error_type = type(e).__name__
                    sanitized_error = f"A {error_type} occurred during search planning"

                    self.printer.update_item(
                        "error",
                        f"Error planning searches: {sanitized_error}",
                        is_done=True,
                    )
                    return

                # Step 2: Perform the searches
                try:
                    # Check if we can restore search results from a previous session
                    session_data = self.persistence.get_session_data(self._session_id)
                    if session_data and session_data.get("status") == "searched" and "search_plan" in session_data:
                        # Restore search plan with results from saved session
                        search_plan = WebSearchPlan.model_validate(session_data["search_plan"])
                        self.printer.update_item(
                            "searching",
                            f"Restored search results from previous session",
                            is_done=True,
                        )
                    else:
                        # Perform new searches
                        search_plan = await self._perform_searches(search_plan)

                        # Update the search_questions with search results
                        if self._session_id and search_questions:
                            # Get the current session data
                            session_data = self.persistence.get_session_data(self._session_id) or {}

                            # Create a new structure for search_questions with results
                            if "search_questions" in session_data:
                                # For each question in the search plan, add the search results
                                for i, search_item in enumerate(search_plan.searches):
                                    # Find the corresponding question in search_questions
                                    if i < len(session_data["search_questions"]["questions"]):
                                        # Add the search results to the question
                                        if hasattr(search_item, "search_results") and search_item.search_results:
                                            # If the question is already a dict with results, update it
                                            if isinstance(session_data["search_questions"]["questions"][i], dict):
                                                session_data["search_questions"]["questions"][i]["results"] = search_item.search_results
                                            else:
                                                # Convert the question from a string to a dict with results
                                                question_text = session_data["search_questions"]["questions"][i]
                                                session_data["search_questions"]["questions"][i] = {
                                                    "question": question_text,
                                                    "results": search_item.search_results
                                                }
                                        else:
                                            # If no search results, create an empty results array
                                            if isinstance(session_data["search_questions"]["questions"][i], dict):
                                                if "results" not in session_data["search_questions"]["questions"][i]:
                                                    session_data["search_questions"]["questions"][i]["results"] = []
                                            else:
                                                # Convert the question from a string to a dict with empty results
                                                question_text = session_data["search_questions"]["questions"][i]
                                                session_data["search_questions"]["questions"][i] = {
                                                    "question": question_text,
                                                    "results": []
                                                }

                            # Update the count in search_questions to reflect the total number of questions
                            if "search_questions" in session_data and "questions" in session_data["search_questions"]:
                                session_data["search_questions"]["count"] = len(session_data["search_questions"]["questions"])

                            # Save the updated session data
                            session_data["status"] = "searched"
                            self.persistence.save_session_data(self._session_id, session_data)
                        else:
                            # Save the updated search plan (old method)
                            self.persistence.save_search_plan(query, search_plan.model_dump())

                    # Extract search results from the search plan
                    search_results = [item.result for item in search_plan.searches if item.result is not None]

                    if not search_results:
                        self.printer.update_item(
                            "warning",
                            "No search results were found. The report may be limited.",
                            is_done=True,
                        )
                    else:
                        # Step 2.5: Generate additional questions based on search results
                        if QuestionGeneratorConfig.USE_SEARCH_RESULTS:
                            try:
                                self.printer.update_item("generating_questions with query:", query)

                                # Generate additional questions using search results
                                additional_questions_result = await self._generate_questions(query, search_results)

                                # Merge with existing questions
                                if search_questions and "questions" in search_questions:
                                    # Get existing questions
                                    existing_questions = search_questions["questions"]

                                    # Add new questions
                                    all_questions = existing_questions + additional_questions_result.questions

                                    # Deduplicate questions
                                    unique_questions = []
                                    for q in all_questions:
                                        if q not in unique_questions:
                                            unique_questions.append(q)

                                    # Update search_questions
                                    search_questions["questions"] = unique_questions
                                    search_questions["count"] = len(unique_questions)

                                    # Save updated questions
                                    if self._session_id:
                                        session_data = self.persistence.get_session_data(self._session_id) or {}
                                        session_data["search_questions"] = search_questions
                                        self.persistence.save_session_data(self._session_id, session_data)

                                    self.printer.update_item(
                                        "generating_questions",
                                        f"Generated {len(additional_questions_result.questions)} additional questions from search results (total: {len(unique_questions)})",
                                        is_done=True,
                                    )
                                else:
                                    # No existing questions, use the new ones
                                    search_questions = additional_questions_result.to_dict()

                                    # Save questions
                                    if self._session_id:
                                        session_data = self.persistence.get_session_data(self._session_id) or {}
                                        session_data["search_questions"] = search_questions
                                        self.persistence.save_session_data(self._session_id, session_data)

                                    self.printer.update_item(
                                        "generating_questions",
                                        f"Generated {len(additional_questions_result.questions)} questions from search results",
                                        is_done=True,
                                    )
                            except Exception as e:
                                # Log the error but continue with the research process
                                error_msg = format_error(e, "additional question generation")
                                self.printer.update_item(
                                    "warning",
                                 #   f"Error generating additional questions: {error_msg}",
                                    "query: {query}",
                                    is_done=True,
                                )
                except Exception as e:
                    # Sanitize error message to avoid exposing sensitive information
                    error_type = type(e).__name__
                    sanitized_error = f"A {error_type} occurred while performing searches"

                    self.printer.update_item(
                        "error",
                        f"Error performing searches: {sanitized_error}",
                        is_done=True,
                    )
                    return

                # Step 3: Mark the research as completed
                try:
                    # Create a simple report with just the summary
                    report = ReportData(
                        short_summary=f"Research Results for '{query}'",
                        model=ModelConfig.get_writer_model()
                    )

                    # Mark the research as completed
                    if self._session_id:
                        self.persistence.save_report(self._session_id, report.model_dump())
                except Exception as e:
                    # Sanitize error message to avoid exposing sensitive information
                    error_type = type(e).__name__
                    sanitized_error = f"A {error_type} occurred while writing the report"

                    self.printer.update_item(
                        "error",
                        f"Error writing report: {sanitized_error}",
                        is_done=True,
                    )
                    return

                # Display a summary of the report
                final_report = f"Report summary\n\n{report.short_summary}"
                self.printer.update_item("final_report", final_report, is_done=True)

                # Display session information
                if self._session_id:
                    self.printer.update_item(
                        "session_info",
                        f"Research session saved: {self._session_id}",
                        is_done=True,
                    )

                # Print the report summary
                print("\n\n=====REPORT SUMMARY=====\n\n")
                print(f"Summary: {report.short_summary}")
            except Exception as e:
                error_msg = format_error(e, "research process")
                self.printer.update_item(
                    "error",
                    f"Unexpected error: {error_msg}",
                    is_done=True,
                )

    async def _generate_questions(self, query: str) -> QuestionGeneratorResult:
        """
        Use the question generator agent to create research questions.

        Args:
            query: The research topic

        Returns:
            QuestionGeneratorResult containing the generated questions
        """
        self.printer.update_item("generating_questions", "Generating research questions...")

        # Generate questions
        result = await generate_questions(query)

        # Update the printer with the number of questions generated
        if result.questions:
            self.printer.update_item(
                "generating_questions",
                f"Generated {len(result.questions)} research questions",
                is_done=True,
            )
        else:
            self.printer.update_item(
                "warning",
                "Failed to generate research questions",
                is_done=True,
            )

        return result

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        """
        Use the planner agent to create a plan of search queries.

        Args:
            query: The research query

        Returns:
            A plan containing search queries and their rationale
        """
        # Get the model being used
        model_name = planner_agent.model

        self.printer.update_item("planning", f"Planning searches using {model_name}...")

        try:
            result = await Runner.run(
                planner_agent,
                f"Query: {query}",
            )

            # Parse the response to get the search plan
            # Pass the original query to use in fallback plan if needed
            search_plan = WebSearchPlan.from_response(str(result.final_output), original_query=query)

            self.printer.update_item(
                "planning",
                f"Will perform {len(search_plan.searches)} searches",
                is_done=True,
            )

            return search_plan
        except Exception as e:
            # Sanitize error message to avoid exposing sensitive information
            error_type = type(e).__name__
            sanitized_error = f"A {error_type} occurred during planning"

            self.printer.update_item(
                "error",
                f"Error planning searches [{model_name}]: {sanitized_error}",
                is_done=True,
            )
            print(f"[{model_name}] Planning error: {error_type}")
            raise e

    async def _perform_searches(self, search_plan: WebSearchPlan) -> WebSearchPlan:
        """
        Execute the search plan by running searches in parallel with rate limiting.

        Args:
            search_plan: The plan containing search queries

        Returns:
            The search plan with results populated
        """
        with custom_span("Search the web"):
            self.printer.update_item("searching", "Searching...")

            # Regular search process with API calls
            # Rate limiting configuration
            max_concurrent_searches = 3  # Maximum number of concurrent searches
            delay_between_searches = 1.0  # Delay in seconds between starting searches
            search_timeout = 60.0  # Timeout for each individual search in seconds
            overall_timeout = 300.0  # Overall timeout for all searches in seconds

            # Create a semaphore to limit concurrent searches
            semaphore = asyncio.Semaphore(max_concurrent_searches)

            async def rate_limited_search(item: WebSearchItem) -> WebSearchItem:
                """Execute a search with rate limiting and timeout."""
                # Add a small delay to prevent API rate limits BEFORE acquiring the semaphore
                # This prevents blocking other tasks while waiting
                await asyncio.sleep(delay_between_searches)

                async with semaphore:  # Limit concurrent searches
                    try:
                        # Apply timeout to individual search
                        search_result = await asyncio.wait_for(self._search(item), timeout=search_timeout)
                        # Store the result in the item
                        item.result = search_result
                        return item
                    except asyncio.TimeoutError:
                        self.printer.update_item(
                            "warning",
                            f"Search for '{item.query}' timed out after {search_timeout} seconds",
                            is_done=True,
                        )
                        # Store the timeout message in the item
                        item.result = f"[Search for '{item.query}' timed out after {search_timeout} seconds]"
                        return item

            num_completed = 0
            tasks = [asyncio.create_task(rate_limited_search(item)) for item in search_plan.searches]

            # Set an overall timeout for all searches
            start_time = time.time()

            try:
                for task in asyncio.as_completed(tasks):
                    # Check if overall timeout has been reached
                    if time.time() - start_time > overall_timeout:
                        self.printer.update_item(
                            "warning",
                            f"Overall search process timed out after {overall_timeout} seconds. Some searches may not have completed.",
                            is_done=True,
                        )
                        # Cancel remaining tasks
                        for t in tasks:
                            if not t.done():
                                t.cancel()
                        break

                    try:
                        # The result is the updated WebSearchItem
                        await task
                        # No need to do anything with the result as the WebSearchItem is updated in-place
                    except asyncio.CancelledError:
                        # Task was cancelled, just skip it
                        pass
                    except Exception as e:
                        error_msg = f"[Search error: {str(e)}]"
                        self.printer.update_item(
                            "error",
                            f"Error in search task: {str(e)}",
                            is_done=True,
                        )
                        # We can't update the WebSearchItem here as we don't know which one failed
                        # Just log the error

                    num_completed += 1
                    self.printer.update_item(
                        "searching", f"Searching... {num_completed}/{len(tasks)} completed"
                    )
            except Exception as e:
                self.printer.update_item(
                    "error",
                    f"Error in search process: {str(e)}",
                    is_done=True,
                )
            finally:
                # Cancel any remaining tasks to prevent resource leaks
                for task in tasks:
                    if not task.done():
                        task.cancel()

                self.printer.mark_item_done("searching")

            return search_plan

    async def _search(self, item: WebSearchItem) -> str:
        """
        Execute a single search and summarize the results.

        Args:
            item: The search item containing query and rationale

        Returns:
            A summary of the search results as a string, or an error message if the search failed
            The item is also updated with the search tool and URLs
        """
        # Limit query length to prevent excessive resource usage
        max_query_length = 200

        if len(item.query) > max_query_length:
            original_query = item.query
            truncated_query = item.query[:max_query_length] + "..."

            # Update the printer with a warning
            self.printer.update_item(
                "warning",
                f"Query truncated due to excessive length: '{truncated_query}'",
                is_done=True,
            )

            # Log the truncation
            print(f"WARNING: Query truncated from {len(original_query)} to {max_query_length} characters")

            # Truncate the query
            item.query = item.query[:max_query_length]

        # No reason field anymore
        input = f"Search term: {item.query}"

        try:
            # Set a timeout for the search operation
            timeout_seconds = 60  # 1 minute timeout per search

            # Try using custom search tools first if available
            if custom_search_tool:
                try:
                    # Use our custom search tool
                    tool_name = custom_search_tool.__class__.__name__
                    print(f"Using {tool_name} for query: {item.query}")

                    # Store the search tool name in the item
                    item.search_tool = tool_name

                    search_task = asyncio.create_task(custom_search_tool.search(item.query))

                    # Wait for the task to complete with a timeout
                    result = await asyncio.wait_for(search_task, timeout=timeout_seconds)

                    # Try to extract URLs and detailed search results if available
                    if hasattr(custom_search_tool, 'last_urls') and custom_search_tool.last_urls:
                        item.urls = custom_search_tool.last_urls

                    # Store detailed search results if available
                    if hasattr(custom_search_tool, 'last_search_results') and custom_search_tool.last_search_results:
                        item.search_results = custom_search_tool.last_search_results

                    # Limit the size of the search result to prevent memory issues
                    max_result_length = 5000  # Limit to 5000 characters

                    if len(result) > max_result_length:
                        original_result_length = len(result)
                        truncated_result = result[:max_result_length] + "\n\n[NOTICE: Result truncated due to excessive length. Original length: " + str(original_result_length) + " characters]"

                        # Update the printer with a warning
                        self.printer.update_item(
                            "warning",
                            f"Search result for '{item.query}' truncated from {original_result_length} to {max_result_length} characters",
                            is_done=True,
                        )

                        # Log the truncation
                        print(f"WARNING: Search result truncated from {original_result_length} to {max_result_length} characters")

                        return truncated_result

                    return result
                except Exception as e:
                    # If custom search fails, log the error and fall back to default search
                    print(f"Custom search failed: {str(e)}. Falling back to default search.")

            # Fall back to default search agent if custom search is not available or failed
            print(f"Using default search agent for query: {item.query}")

            # Store the search tool name in the item
            item.search_tool = "DefaultSearchAgent"

            search_task = asyncio.create_task(Runner.run(
                search_agent,
                input,
            ))

            # Wait for the task to complete with a timeout
            try:
                result = await asyncio.wait_for(search_task, timeout=timeout_seconds)
                output = str(result.final_output)

                # Limit the size of the search result to prevent memory issues
                max_result_length = 5000  # Limit to 5000 characters
                if len(output) > max_result_length:
                    truncated_output = output[:max_result_length] + "\n\n[Result truncated due to excessive length]"
                    self.printer.update_item(
                        "warning",
                        f"Search result for '{item.query}' truncated due to excessive length",
                        is_done=True,
                    )
                    return truncated_output

                return output
            except asyncio.TimeoutError:
                # Handle timeout
                self.printer.update_item(
                    "warning",
                    f"Search for '{item.query}' timed out after {timeout_seconds} seconds",
                    is_done=True,
                )
                print(f"Search timeout for '{item.query}' after {timeout_seconds} seconds")
                return f"[Search for '{item.query}' timed out after {timeout_seconds} seconds]"
        except Exception as e:
            # Sanitize error message to avoid exposing sensitive information
            error_type = type(e).__name__
            sanitized_error = f"A {error_type} occurred during search"

            self.printer.update_item(
                "error",
                f"Error searching for '{item.query}': {sanitized_error}",
                is_done=True,
            )
            # Log the error for debugging (but don't include in user-facing output)
            print(f"Search error for '{item.query}': {error_type}")
            return f"[Error searching for '{item.query}': {sanitized_error}]"

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        """
        Use the writer agent to synthesize search results into a report.

        Args:
            query: The original research query
            search_results: Summaries of search results

        Returns:
            The final report data
        """
        self.printer.update_item("writing", "Thinking about report...")

        # Validate search results before proceeding
        if not search_results:
            self.printer.update_item(
                "warning",
                "No search results available. Cannot generate report.",
                is_done=True,
            )
            print("WARNING: No search results available. Cannot generate report.")

            # Create a fallback report with an error message
            fallback_data = {
                "short_summary": f"ERROR: Failed to generate report for '{query}' (no search results)"
            }
            return ReportData.model_validate(fallback_data)

        # Validate each search result is a string
        validated_results = []
        for i, result in enumerate(search_results):
            if result is None:
                print(f"WARNING: Search result {i} is None, skipping")
                continue

            if not isinstance(result, str):
                print(f"WARNING: Search result {i} is not a string, converting to string: {type(result)}")
                try:
                    result = str(result)
                except Exception as e:
                    print(f"ERROR: Failed to convert search result {i} to string: {e}")
                    continue

            if not result.strip():
                print(f"WARNING: Search result {i} is empty or whitespace, skipping")
                continue

            validated_results.append(result)

        if not validated_results:
            self.printer.update_item(
                "warning",
                "All search results were invalid. Cannot generate report.",
                is_done=True,
            )
            print("WARNING: All search results were invalid. Cannot generate report.")

            # Create a fallback report with an error message
            fallback_data = {
                "short_summary": f"ERROR: Failed to generate report for '{query}' (invalid search results)"
            }
            return ReportData.model_validate(fallback_data)

        # Format the search results in a more structured way
        formatted_results = "\n\n".join([f"Search Result {i+1}:\n{result}" for i, result in enumerate(validated_results)])

        # Regular report generation with API calls
        input = f"Original query: {query}\n\nNumber of search results: {len(validated_results)}\n\nSummarized search results:\n{formatted_results}"

        # Store the input for debugging purposes
        llm_input = input

        # Set a timeout for the report generation
        timeout_seconds = 300  # 5 minutes timeout for report generation

        try:
            # Get the model being used
            model_name = writer_agent.model

            print(f"\n[DEBUG] [{model_name}] Starting report generation...")
            print(f"[DEBUG] [{model_name}] Input type: {type(input)}")
            print(f"[DEBUG] [{model_name}] Input length: {len(input)}")
            print(f"[DEBUG] [{model_name}] Query: {query[:100]}..." if len(query) > 100 else f"[DEBUG] [{model_name}] Query: {query}")
            print(f"[DEBUG] [{model_name}] Search results count: {len(search_results)}")

            # IMPORTANT: The Runner.run_streamed method returns a RunResultStreaming object, not a coroutine
            # Do NOT use 'await' with this method as it will cause a TypeError:
            # "object RunResultStreaming can't be used in 'await' expression"
            # Instead, we process the streaming result directly using its methods
            print(f"[DEBUG] [{model_name}] Calling Runner.run_streamed...")
            result = Runner.run_streamed(
                writer_agent,
                input,
            )
            print(f"[DEBUG] [{model_name}] Runner.run_streamed initialized successfully")

            # Set up a timeout for the report generation
            start_time = time.time()
        except TimeoutError as e:
            raise e
        except Exception as e:
            # Get the model being used
            model_name = writer_agent.model

            # Detailed error logging
            error_type = type(e).__name__
            print(f"\n[DEBUG] [{model_name}] Error in report generation: {error_type}")
            print(f"[DEBUG] [{model_name}] Error message: {str(e)}")
            print(f"[DEBUG] [{model_name}] Error details: {repr(e)}")

            # Print stack trace for debugging
            import traceback
            print(f"[DEBUG] [{model_name}] Stack trace:")
            traceback.print_exc()

            # Sanitize error message for user display
            sanitized_error = f"A {error_type} occurred during report generation"

            self.printer.update_item(
                "error",
                f"Error generating report [{model_name}]: {sanitized_error}",
                is_done=True,
            )
            print(f"[{model_name}] Report generation error: {error_type}")
            raise e

        # Show progress updates while the report is being generated
        update_messages = [
            "Thinking about report...",
            "Planning report structure...",
            "Writing outline...",
            "Creating sections...",
            "Cleaning up formatting...",
            "Finalizing report...",
            "Finishing report...",
        ]

        next_message = 0

        try:
            # Process the streaming result
            final_output = None

            # Set up a task to update progress messages
            async def update_progress():
                nonlocal next_message
                while next_message < len(update_messages):
                    self.printer.update_item("writing", update_messages[next_message])
                    next_message += 1

                    # Add a small delay between updates
                    await asyncio.sleep(5)

                    # Check for timeout
                    current_time = time.time()
                    if current_time - start_time > timeout_seconds:
                        self.printer.update_item(
                            "error",
                            f"Report generation timed out after {timeout_seconds} seconds",
                            is_done=True,
                        )
                        print(f"Report generation timed out after {timeout_seconds} seconds")
                        raise TimeoutError(f"Report generation timed out after {timeout_seconds} seconds")

            # Start the progress update task
            progress_task = asyncio.create_task(update_progress())

            # Get the model being used
            model_name = writer_agent.model

            # Process the streaming result
            try:
                print(f"[DEBUG] [{model_name}] Processing result type: {type(result)}")

                # Check if result has a stream method
                if hasattr(result, 'stream'):
                    print(f"[DEBUG] [{model_name}] Result has stream method, processing stream events")
                    # Initialize final_output to None explicitly
                    final_output = None
                    event_count = 0
                    accumulated_content = ""

                    # Debug the result object
                    result_attrs = [attr for attr in dir(result) if not attr.startswith('_')]
                    print(f"[DEBUG] [{model_name}] Result attributes: {result_attrs}")

                    # Check if result has a final_output attribute
                    if hasattr(result, 'final_output'):
                        print(f"[DEBUG] [{model_name}] Result has final_output attribute: {result.final_output}")
                    else:
                        print(f"[DEBUG] [{model_name}] Result does not have final_output attribute")

                    # Check if result has a message attribute
                    if hasattr(result, 'message'):
                        print(f"[DEBUG] [{model_name}] Result has message attribute: {result.message}")
                    else:
                        print(f"[DEBUG] [{model_name}] Result does not have message attribute")

                    # Process the stream events
                    try:
                        # Create a list to store all event data for debugging
                        all_events_data = []
                        events_debug_info = ""

                        for event in result.stream():
                            event_count += 1
                            print(f"[DEBUG] [{model_name}] Stream event #{event_count}, type: {type(event)}")

                            # Debug the event attributes
                            event_attrs = [attr for attr in dir(event) if not attr.startswith('_')]
                            print(f"[DEBUG] [{model_name}] Event attributes: {event_attrs}")

                            # Store event data for debugging
                            event_data = {
                                'event_num': event_count,
                                'event_type': str(type(event)),
                                'event_attrs': event_attrs,
                                'event_str': str(event)
                            }

                            # Add delta content if available
                            if hasattr(event, 'delta') and event.delta is not None:
                                print(f"[DEBUG] [{model_name}] Event has delta: {event.delta}")
                                event_data['delta'] = str(event.delta)

                                # Accumulate content from deltas
                                if hasattr(event.delta, 'content') and event.delta.content is not None:
                                    delta_content = event.delta.content
                                    accumulated_content += delta_content
                                    event_data['delta_content'] = delta_content
                                    print(f"[DEBUG] [{model_name}] Accumulated content length: {len(accumulated_content)}")

                            # Add to events list
                            all_events_data.append(event_data)

                            if hasattr(event, 'final_output') and event.final_output is not None:
                                print(f"[DEBUG] [{model_name}] Event has final_output: {type(event.final_output)}")
                                final_output = event.final_output
                                event_data['has_final_output'] = True
                                event_data['final_output_type'] = str(type(final_output))
                                print(f"[DEBUG] [{model_name}] Final output set to: {str(final_output)[:100]}..." if len(str(final_output)) > 100 else f"[DEBUG] [{model_name}] Final output set to: {str(final_output)}")
                                break

                        # Store all events data in a variable for later use in the error report
                        events_debug_info = "\n\n## LLM Stream Events\n\n```\n"
                        for i, event_data in enumerate(all_events_data):
                            events_debug_info += f"Event {i+1}:\n"
                            for k, v in event_data.items():
                                events_debug_info += f"  {k}: {v}\n"
                            events_debug_info += "\n"
                        events_debug_info += "```\n"
                    except Exception as e:
                        print(f"[DEBUG] [{model_name}] Error processing stream events: {str(e)}")
                        print(f"[DEBUG] [{model_name}] Error type: {type(e)}")
                        print(f"[DEBUG] [{model_name}] Error traceback: {traceback.format_exc()}")

                    print(f"[DEBUG] [{model_name}] Processed {event_count} stream events")
                    if final_output is None:
                        print(f"[DEBUG] [{model_name}] No event had a non-None final_output")

                        # If we have accumulated content, try to use it
                        if accumulated_content:
                            print(f"[DEBUG] [{model_name}] Using accumulated content as final output")
                            print(f"[DEBUG] [{model_name}] Accumulated content preview: {accumulated_content[:200]}..." if len(accumulated_content) > 200 else f"[DEBUG] [{model_name}] Accumulated content: {accumulated_content}")

                            # Try to parse the accumulated content as JSON
                            try:
                                import json
                                # Check if the accumulated content is valid JSON
                                if accumulated_content.strip().startswith('{') and accumulated_content.strip().endswith('}'):
                                    # Parse the JSON to validate it, but we don't need to use the result
                                    _ = json.loads(accumulated_content)
                                    print(f"[DEBUG] [{model_name}] Successfully parsed accumulated content as JSON")
                                    final_output = accumulated_content
                                else:
                                    print(f"[DEBUG] [{model_name}] Accumulated content is not valid JSON")
                                    final_output = None
                            except json.JSONDecodeError as e:
                                print(f"[DEBUG] [{model_name}] Failed to parse accumulated content as JSON: {str(e)}")
                                final_output = None
                # If not, check if it has a final_output attribute directly
                elif hasattr(result, 'final_output'):
                    print(f"[DEBUG] [{model_name}] Result has final_output attribute")
                    final_output = result.final_output
                else:
                    # If neither, use the result itself as the final output
                    print(f"[DEBUG] [{model_name}] Using result directly as final_output")
                    final_output = result
            except Exception as e:
                print(f"[DEBUG] [{model_name}] Error processing stream: {type(e).__name__}: {str(e)}")
                # Fall back to using the result directly
                final_output = result

            # If final_output is None, use a fallback message
            if final_output is None:
                print(f"[DEBUG] [{model_name}] Final output is None, using fallback message")
                print(f"[DEBUG] [{model_name}] Query for fallback message: '{query}'")

                # Create a generic fallback message based on the query
                # Use title case for the title, which capitalizes each word
                title = ' '.join(word.capitalize() for word in query.strip().split())
                # Special case for common acronyms like AI, ADHD, etc.
                for acronym in ['Ai', 'Adhd', 'Ml', 'Nlp', 'Vr', 'Ar']:
                    title = title.replace(acronym, acronym.upper())
                print(f"[DEBUG] [{model_name}] Fallback title: '{title}'")

                # Add more detailed error information
                error_reason = "unknown error"

                # Check if we have any accumulated content
                if 'accumulated_content' in locals() and accumulated_content:
                    content_preview = accumulated_content[:200] + "..." if len(accumulated_content) > 200 else accumulated_content
                    print(f"[DEBUG] [{model_name}] Accumulated content available: {len(accumulated_content)} characters")
                    print(f"[DEBUG] [{model_name}] Content preview: {content_preview}")
                    error_reason = "incomplete or malformed response"
                else:
                    print(f"[DEBUG] [{model_name}] No accumulated content available")
                    error_reason = "no response received"

                # Check if we have any search results
                if search_results and len(search_results) > 0:
                    print(f"[DEBUG] [{model_name}] Search results available: {len(search_results)} results")
                    error_reason = f"failed to process {len(search_results)} search results"
                else:
                    print(f"[DEBUG] [{model_name}] No search results available")
                    error_reason = "no search results available"

                print(f"[DEBUG] [{model_name}] Error reason: {error_reason}")

                # Get exception information if available
                exception_info = ""
                if 'e' in locals() and e is not None:
                    exception_type = type(e).__name__
                    exception_message = str(e)
                    exception_info = f"\n\n## Exception Details\n\n- **Type**: {exception_type}\n- **Message**: {exception_message}\n"

                    # Add traceback if available
                    try:
                        import traceback
                        tb = traceback.format_exc()
                        exception_info += f"\n\n### Traceback\n\n```\n{tb}\n```\n"
                    except Exception as tb_err:
                        exception_info += f"\n\nFailed to get traceback: {str(tb_err)}"

                # Add information about accumulated content if available
                content_info = ""
                if 'accumulated_content' in locals() and accumulated_content:
                    # Include the entire accumulated content for debugging
                    content_info = f"\n\n## LLM Output Stream (Complete)\n\n```\n{accumulated_content}\n```\n"

                    # Also include a preview for quick reference
                    content_preview = accumulated_content[:500] + "..." if len(accumulated_content) > 500 else accumulated_content
                    content_info += f"\n\n## LLM Output Preview\n\n```\n{content_preview}\n```\n"

                # Add information about search results if available
                search_info = ""
                if search_results and len(search_results) > 0:
                    search_count = len(search_results)
                    # Include the full raw search results data for debugging
                    search_preview = str(search_results[:3]) + "..." if len(search_results) > 3 else str(search_results)

                    # Create a more detailed section with the raw data
                    search_info = f"\n\n## Search Results\n\n- **Count**: {search_count}\n- **Preview**: {search_preview}\n\n### Raw Search Results Data\n\n```\n{str(search_results)}\n```\n"

                # Create a proper title instead of an error message
                error_title = f"Research Results for '{query}'"

                # Create a more detailed error message
                error_message = f"Unable to generate a complete report due to an error in processing the search results: {error_reason}.\n\n"
                error_message += "This is a technical error in the report generation process. The search results were retrieved successfully, "
                error_message += "but there was an error when trying to generate the final report from these results.\n\n"
                error_message += "The complete input sent to the LLM, LLM output stream, and raw search results data are included below for debugging purposes. "
                error_message += "Please try again with a more specific query or check the search results manually."

                # Create a section for the input sent to the LLM
                llm_input_info = ""
                if 'llm_input' in locals() and llm_input is not None:
                    llm_input_info = f"\n\n## Input Sent to LLM\n\n```\n{llm_input}\n```\n"

                # Create a section for raw LLM data
                llm_debug_info = ""
                if 'result' in locals() and result is not None:
                    llm_debug_info = f"\n\n## LLM Result Object\n\n```\n{str(result)}\n```\n"

                # Add events debug info if available
                if 'events_debug_info' in locals():
                    llm_debug_info += events_debug_info

                # Use the LLM input directly as the markdown_report for testing
                fallback_data = {
                    "short_summary": error_title,
                    "markdown_report": llm_input if 'llm_input' in locals() and llm_input is not None else f"# {title}\n\nNo input available.",
                    "follow_up_questions": [
                        f"What specific aspect of {title} are you interested in?",
                        f"Would you like more information about a particular part of {title}?",
                        f"Are there any specific brands or types of {title} you want to learn about?"
                    ]
                }

                # Create a ReportData object directly instead of converting to JSON
                print(f"[DEBUG] [{model_name}] Creating ReportData object directly from fallback data")
                print(f"[DEBUG] [{model_name}] Fallback markdown_report: '{fallback_data['markdown_report']}'")
                return ReportData.model_validate(fallback_data)

            # Cancel the progress update task
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

            # If we get here, the stream completed successfully
            self.printer.mark_item_done("writing")

            # Log the final output for debugging
            print(f"\n[DEBUG] [{model_name}] Stream completed successfully")
            print(f"[DEBUG] [{model_name}] Final output type: {type(final_output)}")

            # If final_output is already a ReportData object, return it directly
            if isinstance(final_output, ReportData):
                return final_output

            # Otherwise, convert to string and parse
            final_output_str = str(final_output)
            print(f"[DEBUG] [{model_name}] Final output length: {len(final_output_str)}")
            print(f"[DEBUG] [{model_name}] Final output preview: {final_output_str[:200]}..." if len(final_output_str) > 200 else f"[DEBUG] [{model_name}] Final output: {final_output_str}")

            # Parse the response using our custom method
            print(f"[DEBUG] [{model_name}] Calling ReportData.from_response...")
            try:
                report_data = ReportData.from_response(final_output_str, model_name)
                print(f"[DEBUG] [{model_name}] ReportData.from_response completed successfully")
                return report_data
            except Exception as e:
                print(f"[DEBUG] [{model_name}] Error in ReportData.from_response: {type(e).__name__}")
                print(f"[DEBUG] [{model_name}] Error message: {str(e)}")
                raise
        except TimeoutError as e:
            raise e
        except Exception as e:
            # Sanitize error message to avoid exposing sensitive information
            error_type = type(e).__name__
            sanitized_error = f"A {error_type} occurred while processing the report"

            self.printer.update_item(
                "error",
                f"Error processing report stream: {sanitized_error}",
                is_done=True,
            )
            print(f"Error processing report stream: {error_type}")
            raise e

    def _merge_questions_into_search_plan(self, search_plan: WebSearchPlan, search_questions: dict) -> WebSearchPlan:
        """
        Merge questions from search_questions into the search plan.

        Args:
            search_plan: The existing search plan
            search_questions: The questions generated by the question generator

        Returns:
            The updated search plan with merged questions
        """
        # Get the existing search items from the plan
        existing_searches = search_plan.searches
        existing_queries = [item.query.lower() for item in existing_searches]

        # Get the topic from search_questions
        topic = search_questions.get("topic", "")

        # Add questions from search_questions that aren't already in the plan
        new_searches = []
        for question in search_questions["questions"]:
            # Extract the question text if it's a dictionary
            if isinstance(question, dict) and "question" in question:
                question_text = question["question"]
            else:
                question_text = question

            # Replace template variables with actual values
            if "{topic}" in question_text and topic:
                question_text = question_text.replace("{topic}", topic)

            # Add the question if it's not already in the plan
            if question_text.lower() not in existing_queries:
                new_searches.append(WebSearchItem(query=question_text))

        # Combine the searches
        if new_searches:
            search_plan.searches.extend(new_searches)

            # Update the count in search_questions to reflect the total number of questions
            # This ensures the count is accurate after merging
            # We need to add the new questions to search_questions as well
            # Make sure to replace any template variables in the questions
            topic = search_questions.get("topic", "")
            for question in new_searches:
                question_text = question.query
                # The template variables should already be replaced in the query,
                # but we'll check again just to be safe
                if "{topic}" in question_text and topic:
                    question_text = question_text.replace("{topic}", topic)
                search_questions["questions"].append(question_text)
            search_questions["count"] = len(search_questions["questions"])

            self.printer.update_item(
                "planning",
                f"Added {len(new_searches)} questions from question generator (total: {len(search_plan.searches)})",
                is_done=True,
            )

        return search_plan
