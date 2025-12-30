import os
import psutil

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
    On other systems, it samples CPU usage over 100ms using psutil and
    computes: logical_cores * (1 - usage/100).

    Returns:
        float: A non-negative float representing approximate available logical
        CPU cores. For example, 2.5 means roughly two and a half cores free.

    Notes:
        - The number of logical cores (with SMT/Hyper-Threading) is used.
        - On Windows and non-POSIX systems, this function blocks for ~100ms
          to collect accurate CPU usage measurements.
        - This is a heuristic; short spikes and scheduling nuances may cause
          deviations from actual availability.
    """

    cnt = psutil.cpu_count(logical=True) or 1

    if os.name != 'nt' and hasattr(os, 'getloadavg'):
        load1 = os.getloadavg()[0]
        return max(cnt - load1, 0.0)  # 0 … cnt cores
    else:
        usage = psutil.cpu_percent(interval=0.1)
        return cnt * (1 - usage / 100.0)


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
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        unused_capacity = 0.0

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            unused_capacity += max(0.0, 100.0 - utilization.gpu)  # Clamp to avoid negative values

        return unused_capacity / 100.0

    except (ModuleNotFoundError, Exception):
        # Return 0.0 if pynvml is not installed, or on any NVML error
        # (no GPUs, driver issues, etc.)
        return 0.0
    finally:
        try:
            import pynvml
            pynvml.nvmlShutdown()
        except:
            pass  # Safe cleanup even if initialization failed
