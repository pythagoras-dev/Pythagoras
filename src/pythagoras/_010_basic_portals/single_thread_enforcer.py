"""Enforcement of single-threaded access to Portals and related classes.

This module contains functionality to ensure that Pythagoras portals
and portal-aware objects are only accessed from the thread
where they were initialized.
"""
from __future__ import annotations

import threading

_portal_thread_id: int | None = None


def _ensure_single_thread() -> None:
    """Enforce single-threaded portal access.

    Pythagoras portals are designed for multi-PROCESS parallelism via
    swarming, not multi-threaded parallelism. Each thread should have
    its own portal instance if thread-based work is needed.

    Raises:
        RuntimeError: If the portal is accessed from a different thread
            than the one where it was initialized.
    """

    global _portal_thread_id
    current_thread_id = threading.current_thread().ident

    if _portal_thread_id is None:
        _portal_thread_id = current_thread_id
    elif _portal_thread_id != current_thread_id:
        raise RuntimeError(
            f"Pythagoras portals are single-threaded by design.\n"
            f"Portal system was initialized on thread {_portal_thread_id}, "
            f"but is now accessed from thread {current_thread_id}.\n"
            f"For parallelism, use swarming (multi-process) instead of threading.\n"
            f"If you need thread-based work, create separate portals per thread.")
