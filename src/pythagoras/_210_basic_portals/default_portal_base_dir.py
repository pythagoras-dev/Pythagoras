"""Utility function to get the default portal base directory."""

from __future__ import annotations

from pathlib import Path


def get_default_portal_base_dir() -> str:
    """Get the base directory for the default local portal.

    Creates the default portal directory (~/.pythagoras/.default_portal) if it
    doesn't exist. This directory is used when no explicit portal is specified.

    Returns:
        The absolute path to the default portal's base directory.

    Example:
        >>> get_default_portal_base_dir()
        '/home/user/.pythagoras/.default_portal'
    """
    home_directory = Path.home()
    target_directory = home_directory / ".pythagoras" / ".default_portal"
    target_directory.mkdir(parents=True, exist_ok=True)
    return str(target_directory.resolve())
