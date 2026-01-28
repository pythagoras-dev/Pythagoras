"""Clear all cache files in the project (for Python, pytest, etc.).

This "test" passes whether or not cache files are found (idempotent behavior).
"""
import pytest
from pathlib import Path

from mixinforge.command_line_tools.basic_file_utils import (
    remove_python_cache_files,
    folder_contains_pyproject_toml,
    format_cache_statistics
)


@pytest.mark.live_actions
def test_live_clear_cache(pytestconfig):
    """Clear cache files.

    Args:
        pytestconfig: Pytest config fixture providing rootdir.
    """
    project_root = Path(pytestconfig.rootdir)

    assert folder_contains_pyproject_toml(project_root), (
        f"pyproject.toml not found at project root: {project_root}")

    # Execute cache clearing on actual project
    try:
        result = remove_python_cache_files(project_root)
    except Exception as e:
        pytest.fail(f"remove_python_cache_files() raised exception: {e}")

    # Validate return structure
    assert isinstance(result, tuple), \
        f"Expected tuple return, got {type(result)}"
    assert len(result) == 2, \
        f"Expected tuple of length 2, got {len(result)}"

    removed_count, removed_items = result

    print("\n")
    print("=" * 70)
    print("🧹 CACHE CLEANUP (Live Action on Project)")
    print("=" * 70)
    output = format_cache_statistics(removed_count, removed_items)
    print(output)
    print("=" * 70)
    print()
