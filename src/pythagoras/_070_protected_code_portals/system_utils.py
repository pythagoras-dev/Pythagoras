import os
import psutil
import pynvml

def get_unused_ram_mb() -> int:
    """Get the currently available RAM on the system in megabytes (MB).

    Returns:
        int: Integer number of megabytes of RAM that are currently available
        to user processes as reported by psutil.virtual_memory().available.

    Notes:
        - The value is rounded down to the nearest integer.
        - Uses powers-of-two conversion (1 MB = 1024^2 bytes).
        - On systems with memory compression or overcommit, this value is an
          approximation provided by the OS.
    """
    free_ram = psutil.virtual_memory().available / (1024 * 1024)
    return int(free_ram)


def get_unused_cpu_cores() -> float:
    """Estimate currently unused logical CPU capacity in units of CPU cores.

    On POSIX systems with load average support, this uses the 1-minute load
    average to estimate remaining capacity: max(logical_cores - load1, 0).
    On other systems, it falls back to instantaneous CPU percent usage as
    reported by psutil and computes: logical_cores * (1 - usage/100).

    Returns:
        float: A non-negative float representing approximate available logical
        CPU cores. For example, 2.5 means roughly two and a half cores free.

    Notes:
        - The number of logical cores (with SMT/Hyper-Threading) is used.
        - If psutil reports near-zero usage, a small default (0.5%) is assumed
          to avoid transient 0.0 readings.
        - This is a heuristic; short spikes and scheduling nuances may cause
          deviations from actual availability.
    """

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
    """Check whether a process with the given PID is currently active.

    Args:
        pid (int): Operating system process identifier (PID).

    Returns:
        bool: True if the process exists and is running; False if it does not
        exist, has exited, or cannot be inspected due to permissions or other
        errors.

    Notes:
        - Any exception from psutil (e.g., NoSuchProcess, AccessDenied) results
          in a False return value for safety.
    """
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except:
        return False


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
    return get_process_start_time(get_current_process_id())


def get_unused_nvidia_gpus() -> float:
    """Estimate the total unused NVIDIA GPU capacity across all devices.

    This aggregates the per-GPU unused utilization percentage (100 - gpu%) and
    returns the sum in "GPU units". For example, 2.0 means capacity equivalent
    to two fully idle GPUs. If no NVIDIA GPUs are present or NVML is unavailable,
    the function returns 0.0.

    Returns:
        float: Sum of unused GPU capacity across all NVIDIA GPUs in GPU units.

    Notes:
        - Requires NVIDIA Management Library (pynvml) to be installed and the
          NVIDIA driver to be available.
        - Utilization is based on instantaneous NVML readings and may fluctuate.
        - Any NVML error (e.g., no devices, driver issues) results in 0.0 for
          safety.
    """
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        unused_capacity = 0.0

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            unused_capacity += max(0.0, 100.0 - utilization.gpu)  # Clamp to avoid negative values

        return unused_capacity / 100.0

    except pynvml.NVMLError:
        # Return 0.0 on any NVML error (no GPUs, driver issues, etc.)
        return 0.0
    finally:
        try:
            pynvml.nvmlShutdown()
        except:
            pass  # Safe cleanup even if initialization failed
