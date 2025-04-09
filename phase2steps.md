# Phase 2 Implementation Steps

This document outlines the step-by-step implementation plan for the Phase 2 requirements of the `reagent` system.

## 1. Question Generator Agent Implementation

### 1.1 Create Question Generator Agent
- [ ] Create `reagents/agents/question_generator_agent.py` file
- [ ] Implement `QuestionGeneratorAgent` class with methods to:
  - Accept a research topic string
  - Generate 40-50 diverse research questions using LLM
  - Ensure questions cover various inquiry types (definitions, causality, comparisons, methods, controversies)
  - Deduplicate and validate questions
  - Return a structured list of questions

### 1.2 Create Prompt Template
- [ ] Create `prompts/question_generation_prompt.txt` file
- [ ] Design a comprehensive prompt that instructs the LLM to:
  - Generate diverse research questions
  - Cover different inquiry types
  - Produce questions that are clear and focused
  - Format output consistently for parsing

### 1.3 Integrate with ResearchManager
- [ ] Modify `reagents/manager.py` to:
  - Initialize the question generator agent
  - Add a new method `_generate_questions(query: str)` to run before the planner step
  - Store results in `research_data["search_questions"]`
  - Update the research flow to include question generation step
  - Ensure persistence of questions in the final JSON output

## 2. CLI Enhancements

### 2.1 Add Questions-Only Mode
- [ ] Modify `main.py` or relevant CLI handler to:
  - Add `--questions-only` flag
  - Implement logic to run only the question generator when flag is present
  - Return and display results without executing planner/search/writer phases

### 2.2 Update Logging
- [ ] Add logging statements in the question generator to:
  - Log the number of questions generated
  - Log sample questions (e.g., first 3-5 questions)
  - Follow existing logging patterns used in other agents

## 3. Testing Implementation

### 3.1 Unit Tests
- [ ] Create `tests/unit/reagents/agents/test_question_generator_agent.py` with tests for:
  - Basic functionality with valid input
  - Edge cases (empty topic, non-string input)
  - Handling of malformed API results
  - Deduplication of similar questions
  - Validation of question format and structure

### 3.2 Integration Tests
- [ ] Create `tests/integration/test_question_generation.py` with tests for:
  - Full workflow integration
  - Verification of `search_questions` in final output
  - Testing the `--questions-only` flag functionality

### 3.3 Mock Data
- [ ] Create mock LLM responses for testing
- [ ] Set up test fixtures for consistent testing

## 4. Documentation Updates

### 4.1 Update README.md
- [ ] Add section on question generation functionality
- [ ] Document the `--questions-only` flag in CLI usage section
- [ ] Explain how question generation enhances research quality
- [ ] Provide examples of generated questions

### 4.2 Developer Documentation
- [ ] Add notes on how to test the question generation module independently
- [ ] Document how to override the default prompt
- [ ] Include examples of expected input/output

## 5. Code Quality Assurance

### 5.1 Ensure Consistent Patterns
- [ ] Review and match logging patterns from other agents
- [ ] Follow configuration patterns used in `planner_agent` and `search_agent`
- [ ] Implement error handling consistent with existing code

### 5.2 Data Validation
- [ ] Ensure UTF-8 compliance for all output
- [ ] Validate that questions are safe for JSON serialization
- [ ] Add sanitization for any user input

## 6. Final Review and Testing

### 6.1 Manual Testing
- [ ] Test the full workflow with various topics
- [ ] Verify questions-only mode works as expected
- [ ] Check output JSON structure and content

### 6.2 Code Review
- [ ] Ensure code meets project standards
- [ ] Verify all requirements from phase2.md are implemented
- [ ] Check for any potential performance issues

### 6.3 Documentation Review
- [ ] Verify all new functionality is properly documented
- [ ] Ensure examples are clear and accurate
- [ ] Check for any missing information

## 7. Deployment Preparation

### 7.1 Final Checks
- [ ] Run all tests to ensure everything passes
- [ ] Verify logging works as expected
- [ ] Check for any runtime errors or warnings

### 7.2 Version Update
- [ ] Update version number if applicable
- [ ] Document changes in changelog or release notes
