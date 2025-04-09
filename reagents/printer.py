from typing import Dict, Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

class Printer:
    """
    Utility class for displaying progress and results in a nice format.
    Uses the rich library for terminal formatting.
    """

    def __init__(self, console: Console):
        self.console: Console = console
        self.items: Dict[str, Dict[str, Any]] = {}
        self.live: Live = Live(self._make_panel(), console=console, refresh_per_second=4)
        self.live.start()
        self._is_running: bool = True

    def __enter__(self):
        """Support for context manager protocol."""
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """Ensure resources are cleaned up when used as a context manager.

        Args:
            exc_type: Exception type if an exception was raised in the context
            exc_val: Exception value if an exception was raised in the context
            exc_tb: Exception traceback if an exception was raised in the context
        """
        try:
            self.end()
        except Exception as e:
            # Log the error but don't suppress the original exception
            print(f"Error cleaning up printer resources: {str(e)}")
        return False  # Don't suppress exceptions

    def update_item(self, key: str, text: str, is_done: bool = False, hide_checkmark: bool = False) -> None:
        """
        Update a progress item with new text.

        Args:
            key: Unique identifier for the item
            text: Text to display
            is_done: Whether the item is completed
            hide_checkmark: Whether to hide the checkmark for completed items
        """
        self.items[key] = {
            "text": text,
            "is_done": is_done,
            "hide_checkmark": hide_checkmark,
        }
        self.live.update(self._make_panel())

    def mark_item_done(self, key: str) -> None:
        """
        Mark an item as completed.

        Args:
            key: Unique identifier for the item
        """
        if key in self.items:
            self.items[key]["is_done"] = True
            self.live.update(self._make_panel())

    def end(self) -> None:
        """End the live display and clean up resources."""
        if self._is_running:
            try:
                self.live.stop()
            except Exception as e:
                print(f"Error stopping live display: {str(e)}")
            finally:
                # Mark as not running even if stop() fails
                self._is_running = False
                # Clear references to help garbage collection
                self.items = {}

    def _make_panel(self) -> Panel:
        """
        Create a panel containing all progress items.

        Returns:
            A rich Panel object for display
        """
        text = Text()

        # Filter out items that contain "query: {query}" or just the query text by itself
        filtered_items = []
        for key, item in self.items.items():
            # Skip items that match the patterns we want to filter out
            if (item["text"] == "query: {query}" or
                item["text"] == "{query}" or
                key == "query" or
                (not key.startswith("0") and not key.startswith("1") and
                 not key.startswith("generating") and not key.startswith("planning") and
                 not key.startswith("searching") and not key.startswith("writing") and
                 not key.startswith("error") and not key.startswith("warning") and
                 not key.startswith("trace") and not key.startswith("resuming") and
                 not key.startswith("basic") and not key.startswith("focused") and
                 not key.startswith("total"))):
                continue
            filtered_items.append((key, item))

        for i, (_, item) in enumerate(filtered_items):
            if i > 0:
                text.append("\n")

            if item["is_done"] and not item["hide_checkmark"]:
                text.append("✓ ", style="green")

            text.append(item["text"])

        return Panel(text, title="Research Progress", border_style="blue")
