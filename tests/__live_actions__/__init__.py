"""Live Actions - "tests" that operate on the actual project.

This package contains live action "tests" that differ from traditional unit tests
in that they operate directly on the actual project files rather than on mocked
or temporary data. These "tests" serve dual purposes:

1. **Validation**: They verify that project maintenance operations work correctly
2. **Execution**: They perform actual maintenance tasks on the project

Examples of live actions include:
- Updating README.md and documentation with project statistics
- Cleaning cache files and temporary directories
- Validating project configuration and structure

## Characteristics:

- **Live**: Operate on real project files (not mocks or temp directories)
- **Self-test**: The project tests and maintains itself
- **CI/CD**: Designed to run in continuous integration pipelines
- **Idempotent**: Safe to run multiple times without side effects
- **Marked**: All tests use `@pytest.mark.live_actions`

## Usage:

Run all live actions:
    pytest -m live_actions

Run all tests except live actions:
    pytest -m "not live_actions"

Run specific live action:
    pytest tests/__live_actions__/clear_cache_live_action.py

## File Naming Convention:

Live action file names follow the pattern: `*_live_action.py`

This distinguishes them from regular unit tests (`test_*.py`) and makes them
immediately recognizable as "tests" that perform actual operations on the project.

## Why a Separate Folder?

Live action "tests" are isolated in `tests/__live_actions__/` because:

- **Distinct purpose**: They maintain the project, not just test isolated units
- **Different nature**: They modify actual project files vs. asserting on test data
- **Special handling**: Can be easily included/excluded from test runs
- **Clear intent**: The folder name signals "these tests do something different"
- **Visual distinction**: Double underscores (`__live_actions__`) make it stand out
"""
