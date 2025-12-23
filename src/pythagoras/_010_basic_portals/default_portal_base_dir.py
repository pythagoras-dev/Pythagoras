"""Utility function to get the default portal base directory."""

from __future__ import annotations

from pathlib import Path


def get_default_portal_base_dir() -> str:
    """Get the base directory for the default local portal.

    The default base directory is ~/.pythagoras/.default_portal

    Pythagoras connects to the default local portal
    when no other portal is specified in the
    program which uses Pythagoras.

    Returns:
        The absolute path to the default portal's base directory as a string.
    """
    home_directory = Path.home()
    target_directory = home_directory / ".pythagoras" / ".default_portal"
    target_directory.mkdir(parents=True, exist_ok=True)
    target_directory_str = str(target_directory.resolve())
    if not isinstance(target_directory_str, str):
        raise TypeError(f"Expected target_directory_str to be str, got {type(target_directory_str).__name__}")
    return target_directory_str
