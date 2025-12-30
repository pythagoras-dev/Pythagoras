import psutil

from .system_processes_info_getters import get_current_process_id, get_current_process_start_time


def process_is_alive(process_id:int, process_start_time:int) -> bool:
    """Check whether a specific process instance is still alive.

    Args:
        process_id: Operating system process identifier (PID).
        process_start_time: Expected UNIX timestamp (seconds) when the process
            started. Used to guard against PID reuse by the OS.

    Returns:
        bool: True only if the process exists, is running (not a zombie), and
        its actual start time matches the expected start time.
    """
    process_start_time = int(process_start_time)
    if process_id <= 0:
        raise ValueError(f"Invalid process ID: {process_id}")
    if process_start_time == 0:
        raise ValueError("Invalid process start time: 0")
    try:
        proc = psutil.Process(process_id)
        if int(proc.create_time()) != process_start_time:
            return False
        elif proc.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
            return False
        return proc.is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False


class DescendantProcessInfo:
    """Lightweight process record: *this* process & its ancestor."""
    process_id: int
    process_start_time: int
    ancestor_process_id: int
    ancestor_process_start_time: int
    process_type: str

    def __init__(self, ancestor_process_id: int, ancestor_process_start_time: int, process_type: str):
        if ancestor_process_start_time == 0:
            raise ValueError("Invalid ancestor process start time: 0")
        self.process_id = get_current_process_id()
        self.process_start_time = get_current_process_start_time()
        self.ancestor_process_id = ancestor_process_id
        self.ancestor_process_start_time = ancestor_process_start_time
        self.process_type = process_type

    def is_alive(self) -> bool:
        """True if *both* this process **and** its ancestor are alive."""
        if process_is_alive(self.process_id, self.process_start_time):
            return process_is_alive(self.ancestor_process_id, self.ancestor_process_start_time)
        return False


    def terminate(self, timeout: float = 3) -> None:
        """Attempt to stop this process safely.

        The method first validates that the PID still refers to the same
        process instance. It then attempts a graceful termination
        and escalates to ``kill`` if the process does not
        exit within the timeout.

        Args:
            timeout (float): Seconds to wait after terminate/kill.
                Defaults to 3 seconds.
        """
        if not self.is_alive():
            return

        try:
            proc = psutil.Process(self.process_id)
            proc.terminate()
            proc.wait(timeout=timeout)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return
        except psutil.TimeoutExpired:
            try:
                proc.kill()
                proc.wait(timeout=timeout)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
