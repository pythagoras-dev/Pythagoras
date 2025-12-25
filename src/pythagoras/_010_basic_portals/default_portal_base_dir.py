"""Utility function to get the default portal base directory."""

from __future__ import annotations

from pathlib import Path


def get_default_portal_base_dir() -> str:
    """Get the base directory for the default local portal.

    The default base directory is ~/.pythagoras/.default_portal
    This function creates the directory if it does not exist.

    Pythagoras connects to the default local portal
    when no other portal is specified in the
    program which uses Pythagoras.

    Returns:
        The absolute path to the default portal's base directory as a string.
    """
    home_directory = Path.home()
    target_directory = home_directory / ".pythagoras" / ".default_portal"
    target_directory.mkdir(parents=True, exist_ok=True)
    return str(target_directory.resolve())
