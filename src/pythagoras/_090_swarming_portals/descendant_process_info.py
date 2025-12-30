"""Lightweight process tracking for descendant processes in the swarm.

Provides utilities to identify and manage processes spawned by a swarming
portal, ensuring correct lifecycle management even when process IDs are
reused by the operating system.
"""

import psutil

from .system_processes_info_getters import get_current_process_id, get_current_process_start_time


def process_is_alive(process_id: int, process_start_time: int) -> bool:
    """Check whether a specific process instance is still alive.

    Uses both PID and start time to uniquely identify the process,
    protecting against false positives when the OS reuses PIDs.

    Args:
        process_id: Operating system process identifier (PID).
        process_start_time: UNIX timestamp in seconds when the process
            started, used to guard against PID reuse.

    Returns:
        True only if the process exists, is running (not a zombie), and
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
    """Tracks a descendant process and its spawning ancestor in a swarm.

    Records both the current process and its ancestor using PID and start
    time pairs to reliably identify process instances across the swarm
    lifecycle. This enables proper cleanup and status checking even when
    PIDs are reused.

    Attributes:
        process_id: PID of the current (descendant) process.
        process_start_time: UNIX timestamp when the current process started.
        ancestor_process_id: PID of the spawning ancestor process.
        ancestor_process_start_time: UNIX timestamp when the ancestor started.
        process_type: Type label identifying the process role in the swarm.
    """
    process_id: int
    process_start_time: int
    ancestor_process_id: int
    ancestor_process_start_time: int
    process_type: str

    def __init__(self, ancestor_process_id: int, ancestor_process_start_time: int, process_type: str):
        """Initialize process info with the current process and its ancestor.

        Args:
            ancestor_process_id: PID of the spawning ancestor process.
            ancestor_process_start_time: UNIX timestamp when ancestor started.
            process_type: Type label for this process's role in the swarm.

        Raises:
            ValueError: If ancestor_process_start_time is 0.
        """
        if ancestor_process_start_time == 0:
            raise ValueError("Invalid ancestor process start time: 0")
        self.process_id = get_current_process_id()
        self.process_start_time = get_current_process_start_time()
        self.ancestor_process_id = ancestor_process_id
        self.ancestor_process_start_time = ancestor_process_start_time
        self.process_type = process_type

    def is_alive(self) -> bool:
        """Check if both this process and its ancestor are alive.

        Returns:
            True only if both the current process and its ancestor are
            running and match their expected start times.
        """
        if process_is_alive(self.process_id, self.process_start_time):
            return process_is_alive(self.ancestor_process_id, self.ancestor_process_start_time)
        return False


    def terminate(self, timeout: float = 3) -> None:
        """Attempt to stop this process gracefully, escalating to kill if needed.

        Validates that the PID still refers to the same process instance
        before attempting termination. First tries graceful SIGTERM,
        escalating to SIGKILL if the process does not exit within the timeout.

        Args:
            timeout: Maximum seconds to wait after each termination attempt.

        Raises:
            ValueError: If timeout is negative.
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
            # Escalate to kill if graceful termination fails
            try:
                proc.kill()
                proc.wait(timeout=timeout)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
