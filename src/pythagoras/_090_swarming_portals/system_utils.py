import os
import psutil

def available_ram_mb() -> int:
    """Returns the amount of available RAM in MB. """
    free_ram = psutil.virtual_memory().available / (1024 * 1024)
    return int(free_ram)


def available_cpu_cores() -> float:
    """Returns the free (logical) CPU capacity"""

    cnt = psutil.cpu_count(logical=True) or 1

    if os.name != 'nt' and hasattr(os, 'getloadavg'):
        load1 = os.getloadavg()[0]
        return max(cnt - load1, 0.0)  # 0 … cnt cores
    else:
        usage = psutil.cpu_percent(interval=None)
        if usage<=0.001:
            usage = 0.5
        return cnt * (1 - usage / 100.0)


def process_is_active(pid: int) -> bool:
    """Checks if a process with the given PID is active."""
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except:
        return False


def process_start_time(pid: int) -> int:
    """Returns the start time of the process with the given PID."""
    try:
        process = psutil.Process(pid)
        return int(process.create_time())
    except:
        return 0


def current_process_id() -> int:
    """Returns the current process ID."""
    return psutil.Process().pid


def current_process_start_time() -> int:
    """Returns the start time of the current process."""
    return process_start_time(current_process_id())


