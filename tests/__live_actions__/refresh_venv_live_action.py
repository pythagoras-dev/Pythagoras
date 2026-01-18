"""Live-on-self CI/CD "test" for refreshing uv.lock file.

This test runs against the actual project to regenerate the uv.lock file
by running `uv sync --upgrade --all-extras`.

The test fails if:
1. pyproject.toml is not found at project root
2. `uv sync --upgrade --all-extras` command fails

The test is idempotent (safe to run multiple times).
"""
import subprocess
import pytest
from pathlib import Path

from mixinforge.command_line_tools.basic_file_utils import (
    folder_contains_pyproject_toml,
)


@pytest.mark.live_actions
def test_live_refresh_venv(pytestconfig):
    """Regenerate uv.lock with uv sync --upgrade --all-extras.

    This is a live-on-self test that:
    - Validates pyproject.toml exists at project root
    - Runs `uv sync --upgrade --all-extras` to regenerate the lock file

    Args:
        pytestconfig: Pytest config fixture providing rootdir.
    """
    project_root = Path(pytestconfig.rootdir)

    # Validate project root contains pyproject.toml
    assert folder_contains_pyproject_toml(project_root), \
        f"pyproject.toml not found at project root: {project_root}"

    uv_lock_path = project_root / "uv.lock"

    # Display results with visual distinction
    print("\n")
    print("=" * 70)
    print("🔄 UV.LOCK REFRESH (Live Action on Project)")
    print("=" * 70)

    print("\n📦 Running: uv sync --upgrade --all-extras")
    print("-" * 70)

    try:
        result = subprocess.run(
            ["uv", "sync", "--upgrade", "--all-extras"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.stdout:
            print(result.stdout)
        print("✓ uv sync --upgrade --all-extras completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        pytest.fail(f"uv sync --upgrade --all-extras failed with return code {e.returncode}")
    except FileNotFoundError:
        pytest.fail("uv command not found. Please install uv first.")

    print("=" * 70)
    print()

    # Verify uv.lock exists
    assert uv_lock_path.exists(), \
        f"uv.lock was not created after uv sync: {uv_lock_path}"
