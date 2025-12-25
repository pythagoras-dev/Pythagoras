"""Enforcement of single-threaded access to Portals and related classes.

This module guarantees that Pythagoras portals and portal-aware objects
are only accessed from the thread where the portal system was first used.
"""

from __future__ import annotations

import inspect
import os
import threading

# Native (OS-level) id of the thread that first accessed the portal layer
_portal_native_id: int | None = None
# Human-readable name of that thread, for diagnostics
_portal_thread_name: str | None = None
# Process id where the above thread was registered
_owner_pid: int | None = None


def _ensure_single_thread() -> None:
    """Raise RuntimeError if the current thread differs from the owner thread.

    Pythagoras supports multi-process (swarming) parallelism, but not
    multi-thread parallelism within a single process. Portals and related
    objects must be accessed exclusively from the thread that first initialized
    the portal system in the current process.
    """
    global _portal_native_id, _portal_thread_name, _owner_pid

    curr_pid = os.getpid()
    curr_native_id = threading.get_native_id()
    curr_name = threading.current_thread().name

    if _owner_pid is not None and curr_pid != _owner_pid:
        # We are in a child process – abandon previous ownership
        _portal_native_id = None
        _portal_thread_name = None
        _owner_pid = None

    if _portal_native_id is None:
        # First use (or first use after fork) – lock the layer to this thread
        _portal_native_id = curr_native_id
        _portal_thread_name = curr_name
        _owner_pid = curr_pid
        return

    if curr_native_id != _portal_native_id:
        caller = inspect.stack()[1]
        raise RuntimeError(
            "Pythagoras portals are single-threaded by design.\n"
            f"Owner thread : {_portal_native_id} ({_portal_thread_name})\n"
            f"Current thread: {curr_native_id} ({curr_name}) at "
            f"{caller.filename}:{caller.lineno}\n"
            "For parallelism use swarming (multi-process).")


def _reset_single_thread_enforcer() -> None:
    """FOR UNIT TESTS ONLY – re-arm the guard for the current process/thread."""
    global _portal_native_id, _portal_thread_name, _owner_pid
    _portal_native_id = None
    _portal_thread_name = None
    _owner_pid = None