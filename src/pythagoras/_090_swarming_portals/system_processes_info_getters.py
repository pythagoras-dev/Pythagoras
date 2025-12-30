"""System process information utilities for swarm process tracking.

Provides lightweight wrappers around psutil for retrieving process IDs
and start times, used to uniquely identify process instances across the
swarm lifecycle.
"""

import psutil


def get_process_start_time(pid: int) -> int:
    """Get the UNIX timestamp when a process started.

    Returns 0 on any error (missing process, permission denied, etc.)
    to provide a safe fallback for process tracking logic.

    Args:
        pid: Operating system process identifier.

    Returns:
        Start time as a UNIX timestamp in seconds, or 0 if the process
        does not exist or cannot be accessed.
    """
    try:
        process = psutil.Process(pid)
        return int(process.create_time())
    except:
        return 0


def get_current_process_id() -> int:
    """Get the current process ID.

    Returns:
        The PID of the running Python process.
    """
    return psutil.Process().pid


def get_current_process_start_time() -> int:
    """Get the UNIX timestamp when the current Python process started.

    Returns:
        Start time as a UNIX timestamp in seconds, or 0 on error.
    """
    return int(get_process_start_time(get_current_process_id()))
