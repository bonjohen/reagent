# Research Agent Tests

This directory contains tests for the Research Agent application.

## Test Structure

- `unit/`: Unit tests for individual components
  - `agents/`: Tests for agent modules
  - `reagents/`: Tests for core reagents modules
- `conftest.py`: Common test fixtures and configuration

## Running Tests

To run all tests:

```bash
pytest
```

To run tests with coverage report:

```bash
pytest --cov=reagents --cov=main --cov-report=term-missing
```

To run a specific test file:

```bash
pytest tests/unit/reagents/test_persistence.py
```

To run a specific test:

```bash
pytest tests/unit/reagents/test_persistence.py::TestResearchPersistence::test_save_search_plan
```

## Test Dependencies

The following dependencies are required for testing:
- pytest
- pytest-asyncio
- pytest-cov

These are included in the project's requirements.txt file.

## Writing New Tests

When writing new tests:

1. Follow the existing structure and naming conventions
2. Use appropriate fixtures from conftest.py
3. Mock external dependencies
4. Test both success and error cases
5. For async functions, use the @pytest.mark.asyncio decorator
