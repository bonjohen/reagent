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
        self.session_id = session_id

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

                self.printer.update_item(
                    "starting",
                    "Starting research...",
                    is_done=True,
                    hide_checkmark=True,
                )

                # Step 1: Plan the searches
                try:
                    # Check if we're resuming from a previous session
                    if self.session_id:
                        session_data = self.persistence.get_session_data(self.session_id)
                        if session_data and session_data.get("status") in ["planned", "searched"]:
                            self.printer.update_item(
                                "resuming",
                                f"Resuming research from previous session {self.session_id}",
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
                                # If no search plan in session, create a new one
                                search_plan = await self._plan_searches(query)
                        else:
                            # Invalid session, create a new search plan
                            search_plan = await self._plan_searches(query)
                    else:
                        # No session ID provided, create a new search plan
                        search_plan = await self._plan_searches(query)

                        # Save the search plan and get a new session ID
                        self.session_id = self.persistence.save_search_plan(
                            query,
                            search_plan.model_dump()
                        )
                        self.printer.update_item(
                            "session",
                            f"Created new research session: {self.session_id}",
                            is_done=True,
                        )
                except Exception as e:
                    error_msg = format_error(e, "planning searches")
                    self.printer.update_item(
                        "error",
                        f"Error planning searches: {error_msg}",
                        is_done=True,
                    )
                    return

                # Step 2: Perform the searches
                try:
                    # Check if we can restore search results from a previous session
                    session_data = self.persistence.get_session_data(self.session_id)
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
                        if self.session_id and search_results:
                            self.persistence.save_search_results(self.session_id, search_results)

                    if not search_results:
                        self.printer.update_item(
                            "warning",
                            "No search results were found. The report may be limited.",
                            is_done=True,
                        )
                except Exception as e:
                    error_msg = format_error(e, "performing searches")
                    self.printer.update_item(
                        "error",
                        f"Error performing searches: {error_msg}",
                        is_done=True,
                    )
                    return

                # Step 3: Write the report
                try:
                    # Check if we can restore the report from a previous session
                    session_data = self.persistence.get_session_data(self.session_id)
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
                        if self.session_id:
                            self.persistence.save_report(self.session_id, report.model_dump())
                except Exception as e:
                    error_msg = format_error(e, "writing report")
                    self.printer.update_item(
                        "error",
                        f"Error writing report: {error_msg}",
                        is_done=True,
                    )
                    return

                # Display a summary of the report
                final_report = f"Report summary\n\n{report.short_summary}"
                self.printer.update_item("final_report", final_report, is_done=True)

                # Display session information
                if self.session_id:
                    self.printer.update_item(
                        "session_info",
                        f"Research session saved: {self.session_id}",
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
        self.printer.update_item("planning", "Planning searches...")

        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )

        # Parse the response to get the search plan
        search_plan = WebSearchPlan.from_response(str(result.final_output))

        self.printer.update_item(
            "planning",
            f"Will perform {len(search_plan.searches)} searches",
            is_done=True,
        )

        return search_plan

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

            # Rate limiting configuration
            max_concurrent_searches = 3  # Maximum number of concurrent searches
            delay_between_searches = 1.0  # Delay in seconds between starting searches
            search_timeout = 60.0  # Timeout for each individual search in seconds
            overall_timeout = 300.0  # Overall timeout for all searches in seconds

            # Create a semaphore to limit concurrent searches
            semaphore = asyncio.Semaphore(max_concurrent_searches)

            async def rate_limited_search(item: WebSearchItem) -> str | None:
                """Execute a search with rate limiting and timeout."""
                async with semaphore:  # Limit concurrent searches
                    # Add a small delay to prevent API rate limits
                    await asyncio.sleep(delay_between_searches)
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
                            results.append(result)
                    except asyncio.CancelledError:
                        # Task was cancelled, just skip it
                        pass
                    except Exception as e:
                        self.printer.update_item(
                            "error",
                            f"Error in search task: {str(e)}",
                            is_done=True,
                        )

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

    async def _search(self, item: WebSearchItem) -> str | None:
        """
        Execute a single search and summarize the results.

        Args:
            item: The search item containing query and rationale

        Returns:
            A summary of the search results, or None if the search failed
        """
        # Limit query length to prevent excessive resource usage
        max_query_length = 200
        if len(item.query) > max_query_length:
            truncated_query = item.query[:max_query_length] + "..."
            self.printer.update_item(
                "warning",
                f"Query truncated due to excessive length: '{truncated_query}'",
                is_done=True,
            )
            item.query = item.query[:max_query_length]

        # Limit reason length as well
        max_reason_length = 500
        if len(item.reason) > max_reason_length:
            item.reason = item.reason[:max_reason_length] + "..."

        input = f"Search term: {item.query}\nReason for searching: {item.reason}"

        try:
            # Set a timeout for the search operation
            timeout_seconds = 60  # 1 minute timeout per search

            # Create a task for the search
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
            self.printer.update_item(
                "error",
                f"Error searching for '{item.query}': {str(e)}",
                is_done=True,
            )
            # Log the error for debugging
            print(f"Search error for '{item.query}': {str(e)}")
            return f"[Error searching for '{item.query}': {str(e)}]"

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

        input = f"Original query: {query}\nSummarized search results: {search_results}"

        # Set a timeout for the report generation
        timeout_seconds = 300  # 5 minutes timeout for report generation

        try:
            # Create a task for the report generation
            # The Runner.run_streamed method returns a coroutine that resolves to a RunResultStreaming object
            # We need to await it to get the actual RunResultStreaming object
            result = await Runner.run_streamed(
                writer_agent,
                input,
            )

            # Set up a timeout for the report generation
            start_time = time.time()
        except TimeoutError as e:
            raise e
        except Exception as e:
            self.printer.update_item(
                "error",
                f"Error generating report: {str(e)}",
                is_done=True,
            )
            print(f"Report generation error: {str(e)}")
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

        last_update = time.time()
        next_message = 0
        timeout_seconds = 300  # 5 minutes timeout

        try:
            # Process the stream events with timeout handling
            async for _ in result.stream_events():
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

                # Update progress messages
                if current_time - last_update > 5 and next_message < len(update_messages):
                    self.printer.update_item("writing", update_messages[next_message])
                    next_message += 1
                    last_update = current_time

            # If we get here, the stream completed successfully
            self.printer.mark_item_done("writing")
            # Parse the response using our custom method
            return ReportData.from_response(str(result.final_output))
        except TimeoutError as e:
            raise e
        except Exception as e:
            self.printer.update_item(
                "error",
                f"Error processing report stream: {str(e)}",
                is_done=True,
            )
            print(f"Error processing report stream: {str(e)}")
            raise e
