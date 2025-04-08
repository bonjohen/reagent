from __future__ import annotations

import asyncio
import time
from typing import Optional

from rich.console import Console

from agents import Runner, custom_span, gen_trace_id, trace

from research_agent.agents.planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from research_agent.agents.search_agent import search_agent
from research_agent.agents.writer_agent import ReportData, writer_agent
from research_agent.printer import Printer
from research_agent.error_utils import format_error
from research_agent.persistence import ResearchPersistence

# Import custom search tools
try:
    from research_agent.tools.search_tools import get_search_tool
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

                # Step 1: Plan the searches
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
                        else:
                            # Invalid session, create a new search plan
                            search_plan = await self._plan_searches(query)
                    else:
                        # No session ID provided, create a new search plan
                        search_plan = await self._plan_searches(query)

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
                    if session_data and session_data.get("status") == "searched" and "search_results" in session_data:
                        # Restore search results from saved session
                        search_results = session_data["search_results"]
                        self.printer.update_item(
                            "searching",
                            f"Restored {len(search_results)} search results from previous session",
                            is_done=True,
                        )
                    else:
                        # Perform new searches
                        search_results = await self._perform_searches(search_plan)

                        # Save the search results
                        if self._session_id and search_results:
                            self.persistence.save_search_results(self._session_id, search_results)

                    if not search_results:
                        self.printer.update_item(
                            "warning",
                            "No search results were found. The report may be limited.",
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

                # Step 3: Write the report
                try:
                    # Check if we can restore the report from a previous session
                    session_data = self.persistence.get_session_data(self._session_id)
                    if session_data and session_data.get("status") == "completed" and "report" in session_data:
                        # Restore report from saved session
                        report_dict = session_data["report"]
                        report = ReportData.model_validate(report_dict)
                        self.printer.update_item(
                            "writing",
                            "Restored report from previous session",
                            is_done=True,
                        )
                    else:
                        # Generate a new report
                        report = await self._write_report(query, search_results)

                        # Save the report
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

                # Print the full report
                print("\n\n=====REPORT=====\n\n")
                print(f"Report: {report.markdown_report}")

                print("\n\n=====FOLLOW UP QUESTIONS=====\n\n")
                follow_up_questions = "\n".join(report.follow_up_questions)
                print(f"Follow up questions: {follow_up_questions}")
            except Exception as e:
                error_msg = format_error(e, "research process")
                self.printer.update_item(
                    "error",
                    f"Unexpected error: {error_msg}",
                    is_done=True,
                )

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

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """
        Execute the search plan by running searches in parallel with rate limiting.

        Args:
            search_plan: The plan containing search queries

        Returns:
            A list of search result summaries
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

            async def rate_limited_search(item: WebSearchItem) -> str | None:
                """Execute a search with rate limiting and timeout."""
                # Add a small delay to prevent API rate limits BEFORE acquiring the semaphore
                # This prevents blocking other tasks while waiting
                await asyncio.sleep(delay_between_searches)

                async with semaphore:  # Limit concurrent searches
                    try:
                        # Apply timeout to individual search
                        return await asyncio.wait_for(self._search(item), timeout=search_timeout)
                    except asyncio.TimeoutError:
                        self.printer.update_item(
                            "warning",
                            f"Search for '{item.query}' timed out after {search_timeout} seconds",
                            is_done=True,
                        )
                        return f"[Search for '{item.query}' timed out after {search_timeout} seconds]"

            num_completed = 0
            tasks = [asyncio.create_task(rate_limited_search(item)) for item in search_plan.searches]
            results = []

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
                        result = await task
                        if result is not None:
                            # Ensure result is a string
                            if not isinstance(result, str):
                                error_msg = f"[Search error: sequence item 0: expected str instance, {type(result).__name__} found]"
                                self.printer.update_item(
                                    "error",
                                    f"Error in search result format: {error_msg}",
                                    is_done=True,
                                )
                                # Convert to string representation
                                results.append(error_msg)
                            else:
                                results.append(result)
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
                        # Add error message to results
                        results.append(error_msg)

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

            return results

    async def _search(self, item: WebSearchItem) -> str:
        """
        Execute a single search and summarize the results.

        Args:
            item: The search item containing query and rationale

        Returns:
            A summary of the search results as a string, or an error message if the search failed
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

        # Limit reason length as well
        max_reason_length = 500

        if len(item.reason) > max_reason_length:
            original_reason = item.reason
            truncated_reason = item.reason[:max_reason_length] + "..."

            # Update the printer with a warning
            self.printer.update_item(
                "warning",
                f"Reason truncated due to excessive length",
                is_done=True,
            )

            # Log the truncation
            print(f"WARNING: Reason truncated from {len(original_reason)} to {max_reason_length} characters")

            # Truncate the reason
            item.reason = truncated_reason

        input = f"Search term: {item.query}\nReason for searching: {item.reason}"

        try:
            # Set a timeout for the search operation
            timeout_seconds = 60  # 1 minute timeout per search

            # Try using custom search tools first if available
            if custom_search_tool:
                try:
                    # Use our custom search tool
                    print(f"Using custom search tool for query: {item.query}")
                    search_task = asyncio.create_task(custom_search_tool.search(item.query))

                    # Wait for the task to complete with a timeout
                    result = await asyncio.wait_for(search_task, timeout=timeout_seconds)

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

        # Regular report generation with API calls
        input = f"Original query: {query}\nSummarized search results: {search_results}"

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
                    for event in result.stream():
                        print(f"[DEBUG] [{model_name}] Stream event type: {type(event)}")

                        if hasattr(event, 'delta') and event.delta is not None:
                            print(f"[DEBUG] [{model_name}] Event has delta: {event.delta}")
                            # Process delta if needed
                            pass

                        if hasattr(event, 'final_output') and event.final_output is not None:
                            print(f"[DEBUG] [{model_name}] Event has final_output: {type(event.final_output)}")
                            final_output = event.final_output
                            break
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
                final_output = {
                    "short_summary": "Error generating report",
                    "markdown_report": "# Latest AI Trends\n\nUnable to generate a complete report due to an error in processing the search results. Please try again with a more specific query or check the search results manually.",
                    "follow_up_questions": [
                        "What specific aspect of AI trends are you interested in?",
                        "Would you like to focus on a particular industry's AI adoption?",
                        "Are you interested in research advancements or commercial applications?"
                    ]
                }
                # Convert the dictionary to a JSON string
                import json
                final_output = json.dumps(final_output)

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
