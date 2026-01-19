"""Live action for cleaning distribution artifacts.

This "test" runs against the actual project to remove distribution artifacts
created by `uv build` (the `dist/` directory).

The test fails if:
1. pyproject.toml is not found at project root
2. An error occurs during deletion

The test passes whether or not the dist/ directory exists (idempotent behavior).
"""
import pytest
from pathlib import Path

from mixinforge.command_line_tools.basic_file_utils import (
    folder_contains_pyproject_toml,
    remove_dist_artifacts,
)
from mixinforge.command_line_tools._cli_entry_points import _format_size


@pytest.mark.live_actions
def test_live_clean_dist(pytestconfig):
    """Remove distribution artifacts (dist/ directory) from the project.

    This is a live-on-self "test" that:
    - Validates pyproject.toml exists at project root
    - Removes the dist/ directory if it exists
    - Passes with or without dist/ present

    Args:
        pytestconfig: Pytest config fixture providing rootdir.
    """
    project_root = Path(pytestconfig.rootdir)

    # Validate project root contains pyproject.toml
    assert folder_contains_pyproject_toml(project_root), \
        f"pyproject.toml not found at project root: {project_root}"

    # Display results with visual distinction
    print("\n")
    print("=" * 70)
    print("DIST CLEANUP (Live Action on Project)")
    print("=" * 70)

    file_count, total_size = remove_dist_artifacts(project_root)

    if file_count > 0:
        size_str = _format_size(total_size)
        print(f"\n Removed dist/ directory ({file_count} files, {size_str})")
    else:
        print("\n No dist/ directory found (already clean)")

    # Verify removal
    dist_path = project_root / "dist"
    assert not dist_path.exists(), \
        f"dist/ directory still exists after removal: {dist_path}"

    print("\n" + "=" * 70)
    print()
