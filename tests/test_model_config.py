"""
Tests for the centralized model configuration.
"""

import pytest
from unittest.mock import patch
from reagents.config import ModelConfig

def test_get_writer_model():
    """Test that get_writer_model returns the primary model by default."""
    model = ModelConfig.get_writer_model()
    assert model == ModelConfig.WRITER_MODEL

def test_get_search_model():
    """Test that get_search_model returns the primary model by default."""
    model = ModelConfig.get_search_model()
    assert model == ModelConfig.SEARCH_MODEL

def test_get_planner_model():
    """Test that get_planner_model returns the primary model by default."""
    model = ModelConfig.get_planner_model()
    assert model == ModelConfig.PLANNER_MODEL

@patch('reagents.config.ModelConfig.WRITER_MODEL', None)
def test_writer_model_fallback():
    """Test that get_writer_model falls back to the fallback model if the primary model is unavailable."""
    with patch('reagents.config.logger') as mock_logger:
        model = ModelConfig.get_writer_model()
        assert model == ModelConfig.WRITER_FALLBACK_MODEL
        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_called_once()

@patch('reagents.config.ModelConfig.SEARCH_MODEL', None)
def test_search_model_fallback():
    """Test that get_search_model falls back to the fallback model if the primary model is unavailable."""
    with patch('reagents.config.logger') as mock_logger:
        model = ModelConfig.get_search_model()
        assert model == ModelConfig.SEARCH_FALLBACK_MODEL
        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_called_once()

@patch('reagents.config.ModelConfig.PLANNER_MODEL', None)
def test_planner_model_fallback():
    """Test that get_planner_model falls back to the fallback model if the primary model is unavailable."""
    with patch('reagents.config.logger') as mock_logger:
        model = ModelConfig.get_planner_model()
        assert model == ModelConfig.PLANNER_FALLBACK_MODEL
        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_called_once()
