"""System process information utilities for swarm process tracking.

Provides lightweight wrappers around psutil for retrieving process IDs
and start times, used to uniquely identify process instances across the
swarm lifecycle.
"""

from time import sleep

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
    except Exception:
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


def get_process_start_time_with_retry(pid: int, max_retries: int = 5, base_delay: float = 0.01) -> int:
    """Get process start time with exponential backoff retry logic to handle race conditions.

    Args:
        pid: Process ID to query
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff (default 0.01)

    Returns:
        Process start time as UNIX timestamp

    Raises:
        RuntimeError: If unable to get valid start time after all retries
    """
    import random
    delay = 0.0
    for attempt in range(max_retries):
        start_time = get_process_start_time(pid)
        if start_time > 0:
            return start_time
        if attempt < max_retries - 1:
            # Exponential backoff with jitter: base_delay * 2^attempt * random(0.5, 1.5)
            delay += base_delay * (2 ** attempt) * random.uniform(0.5, 1.25)
            sleep(delay)
    raise RuntimeError(f"Failed to get start time for process {pid} after {max_retries} attempts")
