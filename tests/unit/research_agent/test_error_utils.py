"""
Unit tests for the error_utils module.
"""
import pytest
from research_agent.error_utils import format_error


class TestErrorUtils:
    """Tests for the error_utils module."""

    def test_format_error_with_context(self):
        """Test formatting an error with context."""
        try:
            # Raise an exception
            raise ValueError("Test error message")
        except Exception as e:
            # Format the error
            error_message = format_error(e, context="Test context")
            
            # Check the formatted message
            assert "Test context" in error_message
            assert "ValueError" in error_message
            assert "Test error message" in error_message

    def test_format_error_without_context(self):
        """Test formatting an error without context."""
        try:
            # Raise an exception
            raise RuntimeError("Another test error")
        except Exception as e:
            # Format the error without context
            error_message = format_error(e)
            
            # Check the formatted message
            assert "Error" in error_message
            assert "RuntimeError" in error_message
            assert "Another test error" in error_message

    def test_format_error_with_nested_exception(self):
        """Test formatting an error with a nested exception."""
        try:
            try:
                # Raise an inner exception
                raise ValueError("Inner error")
            except Exception as inner_e:
                # Raise an outer exception with the inner one as cause
                raise RuntimeError("Outer error") from inner_e
        except Exception as e:
            # Format the error
            error_message = format_error(e, context="Nested test")
            
            # Check the formatted message
            assert "Nested test" in error_message
            assert "RuntimeError" in error_message
            assert "Outer error" in error_message
            # The inner exception should also be included
            assert "ValueError" in error_message
            assert "Inner error" in error_message
