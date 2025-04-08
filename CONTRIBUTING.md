# Contributing to Research Agent

Thank you for your interest in contributing to the Research Agent project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Requests](#pull-requests)
- [Coding Standards](#coding-standards)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/research-agent.git
   cd research-agent
   ```
3. Add the original repository as an upstream remote:
   ```bash
   git remote add upstream https://github.com/originalowner/research-agent.git
   ```
4. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv_reagent
   ```

2. Activate the virtual environment:
   - Windows:
     ```bash
     venv_reagent\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv_reagent/bin/activate
     ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Set up environment variables:
   - Windows:
     ```bash
     setx OPENAI_API_KEY "your-api-key-here"
     ```
   - macOS/Linux:
     ```bash
     export OPENAI_API_KEY="your-api-key-here"
     ```

## Making Changes

1. Make sure your branch is up to date with the upstream main branch:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Make your changes, following the [coding standards](#coding-standards)

3. Commit your changes with a descriptive commit message:
   ```bash
   git commit -m "Add feature: description of your changes"
   ```

4. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

## Testing

1. Run the tests to ensure your changes don't break existing functionality:
   ```bash
   pytest
   ```

2. Add tests for any new functionality you've added

3. Run the linters to ensure code quality:
   ```bash
   flake8
   black .
   isort .
   mypy .
   ```

## Pull Requests

1. Create a pull request from your fork to the original repository

2. In your pull request description, explain:
   - What changes you've made
   - Why you've made these changes
   - Any issues or pull requests that are related

3. Wait for a maintainer to review your pull request

4. Address any feedback or requested changes

5. Once approved, your pull request will be merged

## Coding Standards

We follow these coding standards:

1. **PEP 8**: Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code

2. **Type Hints**: Use type hints for all function parameters and return values

3. **Docstrings**: Include docstrings for all modules, classes, and functions using the Google style:
   ```python
   def function(param1: str, param2: int) -> bool:
       """
       Brief description of the function.
       
       Args:
           param1: Description of param1
           param2: Description of param2
           
       Returns:
           Description of return value
           
       Raises:
           ValueError: When and why this exception is raised
       """
       # Function implementation
   ```

4. **Code Formatting**: We use Black for code formatting and isort for import sorting

5. **Linting**: We use flake8 for linting and mypy for type checking

## Documentation

1. Update documentation for any changes you make to the code

2. If you add new features, include:
   - User documentation in `docs/USER_GUIDE.md`
   - Technical documentation in docstrings
   - Examples of how to use the feature

3. If you fix a bug, update the `docs/TROUBLESHOOTING.md` file if applicable

## Issue Reporting

If you find a bug or have a suggestion for improvement:

1. Check the [GitHub Issues](https://github.com/originalowner/research-agent/issues) to see if it has already been reported

2. If not, create a new issue with:
   - A clear title
   - A detailed description
   - Steps to reproduce (for bugs)
   - Expected and actual behavior (for bugs)
   - Screenshots if applicable
   - Any relevant logs or error messages

## Feature Requests

We welcome feature requests! To suggest a new feature:

1. Create a new issue with the label "feature request"

2. Describe the feature you'd like to see

3. Explain why this feature would be useful

4. If possible, outline how this feature might be implemented

Thank you for contributing to the Research Agent project!
