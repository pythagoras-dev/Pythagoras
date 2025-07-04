import os
import psutil
import pynvml

def get_unused_ram_mb() -> int:
    """Returns the amount of available RAM in MB. """
    free_ram = psutil.virtual_memory().available / (1024 * 1024)
    return int(free_ram)


def get_unused_cpu_cores() -> float:
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


def get_process_start_time(pid: int) -> int:
    """Returns the start time of the process with the given PID."""
    try:
        process = psutil.Process(pid)
        return int(process.create_time())
    except:
        return 0


def get_current_process_id() -> int:
    """Returns the current process ID."""
    return psutil.Process().pid


def get_current_process_start_time() -> int:
    """Returns the start time of the current process."""
    return get_process_start_time(get_current_process_id())


def get_unused_nvidia_gpus() -> float:
    """Returns the total unused GPU capacity as a float value.

    The function calculates the sum of unused capacity across all available NVIDIA GPUs.
    For example, 2.0 means two completely unused GPUs
    0 is returned if no GPUs or on error.
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

    except pynvml.NVMLError as e:
        # Return 0.0 on any NVML error (no GPUs, driver issues, etc.)
        return 0.0
    finally:
        try:
            pynvml.nvmlShutdown()
        except:
            pass  # Safe cleanup even if initialization failed
