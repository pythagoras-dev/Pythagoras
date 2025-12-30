import psutil


def get_process_start_time(pid: int) -> int:
    """Get the UNIX timestamp of when a process started.

    Args:
        pid (int): Operating system process identifier (PID).

    Returns:
        int: Start time as a UNIX timestamp (seconds since epoch). Returns 0 if
        the process does not exist or cannot be accessed.

    Notes:
        - Any exception from psutil (e.g., NoSuchProcess, AccessDenied) results
          in a 0 return value for safety.
    """
    try:
        process = psutil.Process(pid)
        return int(process.create_time())
    except:
        return 0


def get_current_process_id() -> int:
    """Get the current process ID (PID).

    Returns:
        int: The PID of the running Python process.
    """
    return psutil.Process().pid


def get_current_process_start_time() -> int:
    """Get the UNIX timestamp for when the current Python process started.

    Returns:
        int: Start time as a UNIX timestamp (seconds since epoch). Returns 0 on
        unexpected error.
    """
    return int(get_process_start_time(get_current_process_id()))
