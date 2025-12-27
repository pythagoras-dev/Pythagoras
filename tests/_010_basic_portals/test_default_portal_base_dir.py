"""Tests for default_portal_base_dir utility function."""

from pathlib import Path

from pythagoras import get_default_portal_base_dir


def test_get_default_portal_base_dir_returns_string():
    """Verify get_default_portal_base_dir returns a string path."""
    result = get_default_portal_base_dir()
    assert isinstance(result, str)


def test_get_default_portal_base_dir_creates_directory():
    """Verify the function creates the directory if it doesn't exist."""
    result = get_default_portal_base_dir()
    path = Path(result)
    assert path.exists()
    assert path.is_dir()


def test_get_default_portal_base_dir_path_structure():
    """Verify the returned path follows expected structure."""
    result = get_default_portal_base_dir()
    path = Path(result)

    # Should end with .pythagoras/.default_portal
    assert path.name == ".default_portal"
    assert path.parent.name == ".pythagoras"

    # Should be under user's home directory
    assert Path.home() in path.parents


def test_get_default_portal_base_dir_is_absolute():
    """Verify the returned path is absolute."""
    result = get_default_portal_base_dir()
    path = Path(result)
    assert path.is_absolute()


def test_get_default_portal_base_dir_idempotent():
    """Verify multiple calls return the same path."""
    first_call = get_default_portal_base_dir()
    second_call = get_default_portal_base_dir()
    assert first_call == second_call
