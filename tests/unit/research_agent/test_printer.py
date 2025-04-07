"""
Unit tests for the printer module.
"""
import pytest
from unittest.mock import MagicMock, patch

from research_agent.printer import Printer


class TestPrinter:
    """Tests for the Printer class."""

    def test_init(self, mock_console):
        """Test that the constructor initializes the printer correctly."""
        printer = Printer(mock_console)
        
        assert printer.console == mock_console
        assert isinstance(printer.items, dict)
        assert printer.items == {}
        assert printer._is_running is True
        
        # Check that the live display was started
        mock_console.assert_not_called()  # Console itself shouldn't be called
        assert hasattr(printer, 'live')
        assert printer.live.start.called

    def test_context_manager(self, mock_console):
        """Test that the printer works as a context manager."""
        with Printer(mock_console) as printer:
            assert printer._is_running is True
            
        # After exiting the context, the printer should be stopped
        assert printer._is_running is False
        assert printer.live.stop.called

    def test_context_manager_with_exception(self, mock_console):
        """Test that the printer handles exceptions in the context manager."""
        # Mock the stop method to raise an exception
        with patch.object(Printer, 'end', side_effect=Exception("Test exception")):
            try:
                with Printer(mock_console) as printer:
                    raise ValueError("Test error")
            except ValueError:
                # The ValueError should be propagated
                pass
            
            # Despite the exception in end(), the context manager should not suppress the original exception

    def test_update_item(self, mock_console):
        """Test updating an item in the printer."""
        printer = Printer(mock_console)
        
        # Update an item
        printer.update_item("test_key", "Test message", is_done=False)
        
        # Check that the item was added to the items dict
        assert "test_key" in printer.items
        assert printer.items["test_key"]["text"] == "Test message"
        assert printer.items["test_key"]["is_done"] is False
        assert printer.items["test_key"]["hide_checkmark"] is False
        
        # Check that the live display was updated
        assert printer.live.update.called

    def test_mark_item_done(self, mock_console):
        """Test marking an item as done."""
        printer = Printer(mock_console)
        
        # Add an item
        printer.update_item("test_key", "Test message", is_done=False)
        
        # Mark it as done
        printer.mark_item_done("test_key")
        
        # Check that the item was marked as done
        assert printer.items["test_key"]["is_done"] is True
        
        # Check that the live display was updated
        assert printer.live.update.call_count == 2  # Once for update_item, once for mark_item_done

    def test_mark_nonexistent_item_done(self, mock_console):
        """Test marking a nonexistent item as done."""
        printer = Printer(mock_console)
        
        # Mark a nonexistent item as done
        printer.mark_item_done("nonexistent_key")
        
        # Nothing should happen, and no exception should be raised
        assert "nonexistent_key" not in printer.items
        assert printer.live.update.call_count == 0

    def test_end(self, mock_console):
        """Test ending the printer."""
        printer = Printer(mock_console)
        
        # End the printer
        printer.end()
        
        # Check that the live display was stopped
        assert printer.live.stop.called
        assert printer._is_running is False
        
        # Check that items were cleared
        assert printer.items == {}

    def test_end_already_stopped(self, mock_console):
        """Test ending the printer when it's already stopped."""
        printer = Printer(mock_console)
        
        # End the printer once
        printer.end()
        
        # Reset the mock to check if it's called again
        printer.live.stop.reset_mock()
        
        # End the printer again
        printer.end()
        
        # Check that stop wasn't called again
        assert not printer.live.stop.called

    def test_end_with_exception(self, mock_console):
        """Test that end() handles exceptions gracefully."""
        printer = Printer(mock_console)
        
        # Make stop raise an exception
        printer.live.stop.side_effect = Exception("Test exception")
        
        # End should handle the exception
        printer.end()
        
        # The printer should still be marked as not running
        assert printer._is_running is False
        
        # Items should still be cleared
        assert printer.items == {}

    def test_make_panel(self, mock_console):
        """Test the _make_panel method."""
        printer = Printer(mock_console)
        
        # Add some items
        printer.update_item("key1", "Message 1", is_done=True)
        printer.update_item("key2", "Message 2", is_done=False)
        printer.update_item("key3", "Message 3", is_done=True, hide_checkmark=True)
        
        # Get the panel
        panel = printer._make_panel()
        
        # Check that the panel was created
        assert panel is not None
        assert panel.title == "Research Progress"
        assert panel.border_style == "blue"
        
        # We can't easily check the content of the panel, but we can check that it was created
