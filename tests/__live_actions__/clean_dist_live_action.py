"""Live-on-self CI/CD "test" for cleaning distribution artifacts.

This test runs against the actual project to remove distribution artifacts
created by `uv build` (the `dist/` directory).

The test fails if:
1. pyproject.toml is not found at project root
2. An error occurs during deletion

The test passes whether or not the dist/ directory exists (idempotent behavior).
"""
import shutil
import pytest
from pathlib import Path

from mixinforge.command_line_tools.basic_file_utils import (
    folder_contains_pyproject_toml,
)


@pytest.mark.live_actions
def test_live_clean_dist(pytestconfig):
    """Remove distribution artifacts (dist/ directory) from the project.

    This is a live-on-self test that:
    - Validates pyproject.toml exists at project root
    - Removes the dist/ directory if it exists
    - Is idempotent (passes with or without dist/ present)

    Args:
        pytestconfig: Pytest config fixture providing rootdir.
    """
    project_root = Path(pytestconfig.rootdir)

    # Validate project root contains pyproject.toml
    assert folder_contains_pyproject_toml(project_root), \
        f"pyproject.toml not found at project root: {project_root}"

    dist_path = project_root / "dist"

    # Display results with visual distinction
    print("\n")
    print("=" * 70)
    print("🗑️  DIST CLEANUP (Live Action on Project)")
    print("=" * 70)

    if dist_path.exists():
        # Collect info before deletion
        files_removed = []
        total_size = 0

        for item in dist_path.rglob("*"):
            if item.is_file():
                files_removed.append(item.relative_to(project_root))
                total_size += item.stat().st_size

        # Remove the dist directory
        try:
            shutil.rmtree(dist_path)
        except Exception as e:
            pytest.fail(f"Failed to remove dist/ directory: {e}")

        # Verify removal
        assert not dist_path.exists(), \
            f"dist/ directory still exists after removal: {dist_path}"

        # Format size
        if total_size >= 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.2f} MB"
        elif total_size >= 1024:
            size_str = f"{total_size / 1024:.2f} KB"
        else:
            size_str = f"{total_size} bytes"

        print(f"\n✓ Removed dist/ directory")
        print(f"  Files removed: {len(files_removed)}")
        print(f"  Total size freed: {size_str}")
        print("\n  Removed files:")
        for f in sorted(files_removed):
            print(f"    - {f}")
    else:
        print("\n✓ No dist/ directory found (already clean)")

    print("\n" + "=" * 70)
    print()
