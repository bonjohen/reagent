# Phase 2: Requirements

This document outlines the second-phase feature set for the `reagent` system, focusing on enhancements to the core research workflow and preparation for future RE-* modes (REport, REquirements, REcommendations, REst).

---

## 1. Question Generator Agent Integration

### 1.1 Functionality
- Accept a user-provided research topic string.
- Generate a diverse set of 20–30 research-focused questions using LLM.
- Questions must include varied inquiry types that are appropriate for the topic: definitions, causality, comparisons, methods, controversies, etc.

### 1.2 Placement
- Agent implemented as: `research_agent/agents/question_generator_agent.py`
- Integrated into `ResearchManager` before the planner step.
- Leave the agents/search_agent.py unchanged.

### 1.3 Output
- Results stored in `research_data["search_questions"]`.
- Included in final `research.json` output.

---

## 2. CLI Enhancements

### 2.1 Optional Modes
- Add `--questions-only` flag to run just the question generator without executing planner/search/writer phases.

### 2.2 Logging
- Log number of generated questions and sample entries.

---

## 3. Prompt Management

### 3.1 Prompt Template Storage
- Externalize the prompt string to `prompts/question_generation_prompt.txt`.
- Load dynamically from disk, following the same convention as other agents.

---

## 4. Testing

### 4.1 Unit Tests
- Validate that a list of properly formatted, deduplicated questions is returned.
- Check edge case inputs: empty topic, non-string, malformed API result.

### 4.2 Integration Test
- Run full flow with a test topic, assert presence and structure of `search_questions` in the final output.

---

## 5. Documentation

### 5.1 README Updates
- Document new behavior in the CLI usage section.
- Add section explaining how question generation enhances research quality.

### 5.2 Developer Notes
- Mention how to test the question generation module independently.
- Provide examples of how to override the prompt.

---

## 6. Code Quality

- Match logging and config patterns used in `planner_agent` and `search_agent`.
- Validate UTF-8 compliance for all output.
- Ensure questions are safe for JSON serialization.

---

