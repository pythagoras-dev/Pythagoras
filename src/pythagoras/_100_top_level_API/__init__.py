"""Top-level, user-facing API shortcuts.

This subpackage exposes the easiest entry points for application authors,
primarily constructors and helpers to obtain a portal and interact with it.

Exports:
  top_level_API: Functions that construct and return a portal (e.g., get_portal).
  default_local_portal: Defaults and helpers for creating a local portal
  when not explicitly created/provided by an application that uses Pythagoras.
"""

from .top_level_API import *
from .default_local_portal import *