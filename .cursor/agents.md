# Parallel Agent Workflow

This document defines how to structure multi-agent parallel work in Cursor using a STEP/AGENT naming convention for todo items.

---

## Todo Naming Convention

**Format:** `STEP{N} - {AgentName}: {description}`

- **STEP{N}** - Sequential phase number (STEP1 must complete before STEP2 begins)
- **{AgentName}** - Specialized agent assigned to the task (see Agent Definitions below)

### Examples

```
STEP1 - CodeAgent: Implement core data models
STEP1 - TestAgent: Create unit test scaffolding
STEP1 - DocsAgent: Add module docstrings
STEP2 - CodeAgent: Wire up service layer (waits for STEP1)
STEP2 - TestAgent: Implement unit tests for models
```

---

## Agent Definitions

### CodeAgent
**Role:** Implementation
**Specialization:** Core logic, models, services, business rules

**Responsibilities:**
- Implement new features and functionality
- Create/modify models, services, and utilities
- Handle core business logic implementation

**File Patterns:** `*.py` (excluding tests), `models.py`, `service.py`, `utils/`

---

### TestAgent
**Role:** Quality Assurance
**Specialization:** Unit tests, integration tests, test fixtures

**Responsibilities:**
- Create test scaffolding and fixtures
- Implement unit and integration tests
- Ensure code coverage for new features

**File Patterns:** `tests/`, `test_*.py`, `*_test.py`, `conftest.py`

---

### DocsAgent
**Role:** Documentation
**Specialization:** Docstrings, README, type hints, inline comments

**Responsibilities:**
- Add/update docstrings for modules, classes, and functions
- Maintain README and user-facing documentation
- Ensure comprehensive type hints
- Add clarifying inline comments where needed

**File Patterns:** `*.md`, `docs/`, docstrings in `*.py`

---

### RefactorAgent
**Role:** Code Quality
**Specialization:** Cleanup, DRY, optimization, code organization

**Responsibilities:**
- Refactor for clarity and maintainability
- Apply DRY principles (Don't Repeat Yourself)
- Optimize performance where appropriate
- Reorganize code structure

**File Patterns:** Any `*.py` files requiring cleanup

---

### ConfigAgent
**Role:** Infrastructure
**Specialization:** Dependencies, configs, CI/CD, tooling

**Responsibilities:**
- Manage `pyproject.toml`, `requirements.txt`
- Configure linters, formatters, pre-commit hooks
- Set up CI/CD workflows
- Handle environment and configuration files

**File Patterns:** `pyproject.toml`, `*.toml`, `*.yaml`, `.github/`, `.pre-commit-config.yaml`

---

## Execution Rules

1. **Parallel within STEP**: All agent tasks in the same STEP can run simultaneously
2. **Sequential between STEPs**: STEP{N+1} waits for ALL STEP{N} tasks to complete
3. **No cross-dependencies**: Agents in the same STEP must NOT depend on each other's output
4. **Handoff protocol**: When a STEP completes, review and commit changes before starting next STEP
5. **Conflict avoidance**: Agents in the same STEP should work on different files when possible

---

## Task Assignment Templates

### Template: New Feature Implementation

```
### STEP1 - Foundation (Parallel)
- STEP1 - CodeAgent: Implement core data models for {feature}
- STEP1 - TestAgent: Create test scaffolding and fixtures
- STEP1 - DocsAgent: Add module-level docstrings

### STEP2 - Integration (Parallel, after STEP1)
- STEP2 - CodeAgent: Implement service layer for {feature}
- STEP2 - TestAgent: Write unit tests for models

### STEP3 - Polish (Parallel, after STEP2)
- STEP3 - TestAgent: Add integration tests
- STEP3 - DocsAgent: Update README with usage examples
- STEP3 - RefactorAgent: Code cleanup and optimization
```

---

### Template: Bug Fix

```
### STEP1 - Investigation (Parallel)
- STEP1 - CodeAgent: Identify root cause and implement fix
- STEP1 - TestAgent: Create regression test for the bug

### STEP2 - Validation (Parallel, after STEP1)
- STEP2 - TestAgent: Verify fix doesn't break existing tests
- STEP2 - DocsAgent: Document the fix if user-facing
```

---

### Template: Refactoring

```
### STEP1 - Preparation (Parallel)
- STEP1 - TestAgent: Ensure comprehensive test coverage exists
- STEP1 - DocsAgent: Document current behavior

### STEP2 - Refactor (Sequential recommended)
- STEP2 - RefactorAgent: Apply refactoring changes

### STEP3 - Validation (Parallel, after STEP2)
- STEP3 - TestAgent: Verify all tests pass
- STEP3 - DocsAgent: Update documentation for changes
```

---

## Usage Example

When assigning a task to create a new validation feature:

```markdown
## Task: Add ZIP Code Validation

### STEP1 - Foundation (Parallel)
- STEP1 - CodeAgent: Create ZipCodeValidator class in validation/validators.py
- STEP1 - TestAgent: Set up test file tests/test_zip_validation.py with fixtures
- STEP1 - DocsAgent: Add docstrings to validation module

### STEP2 - Implementation (Parallel, after STEP1)
- STEP2 - CodeAgent: Implement validation logic with US/CA format support
- STEP2 - TestAgent: Write unit tests for valid/invalid ZIP formats

### STEP3 - Finalization (Parallel, after STEP2)
- STEP3 - TestAgent: Add edge case and integration tests
- STEP3 - DocsAgent: Update README with ZIP validation examples
- STEP3 - ConfigAgent: Ensure no new dependencies needed
```

---

## Best Practices

1. **Keep agents focused**: Each agent should have a clear, non-overlapping responsibility
2. **Minimize file conflicts**: Plan which agent modifies which files to avoid merge conflicts
3. **Commit between steps**: Review and commit after each STEP completes
4. **Start simple**: For small tasks, use fewer agents and steps
5. **Scale up gradually**: Add more parallel agents only when the task complexity warrants it
