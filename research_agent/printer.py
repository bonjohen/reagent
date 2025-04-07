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

    def __exit__(self, *_):
        """Ensure resources are cleaned up when used as a context manager."""
        self.end()

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
                self._is_running = False

    def _make_panel(self) -> Panel:
        """
        Create a panel containing all progress items.

        Returns:
            A rich Panel object for display
        """
        text = Text()

        for i, (_, item) in enumerate(self.items.items()):
            if i > 0:
                text.append("\n")

            if item["is_done"] and not item["hide_checkmark"]:
                text.append("✓ ", style="green")

            text.append(item["text"])

        return Panel(text, title="Research Progress", border_style="blue")
