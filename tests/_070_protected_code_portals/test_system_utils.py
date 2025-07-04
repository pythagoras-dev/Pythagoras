import os
import time
import multiprocessing as mp

import psutil
import pynvml

from pythagoras._070_protected_code_portals.system_utils import (
    get_unused_ram_mb,
    get_unused_cpu_cores,
    process_is_active,
    get_process_start_time,
    get_current_process_id,
    get_current_process_start_time,
    get_unused_nvidia_gpus,
)



# ---------------------------------------------------------------------------
# Basic semantics (from previous answer)
# ---------------------------------------------------------------------------

def test_available_ram_is_int_and_within_bounds():
    avail = get_unused_ram_mb()
    total = psutil.virtual_memory().total // (1024 * 1024)
    assert isinstance(avail, int)
    assert 0 <= avail <= total


def test_available_cpu_cores_range_and_type():
    free_cores = get_unused_cpu_cores()
    logical_cnt = psutil.cpu_count(logical=True) or 1
    assert isinstance(free_cores, (float, int))
    assert 0.0 <= free_cores <= float(logical_cnt)


def test_current_pid_consistency():
    pid = get_current_process_id()
    assert pid == os.getpid() == psutil.Process().pid
    assert pid > 0


def test_process_is_active_truth_table():
    this_pid = get_current_process_id()
    assert process_is_active(this_pid) is True

    bogus_pid = -42 if os.name != "nt" else 999_999_999
    assert process_is_active(bogus_pid) is False


def test_process_start_time_values():
    now = int(time.time())
    this_pid = get_current_process_id()

    start_ts = get_process_start_time(this_pid)
    assert 0 < start_ts <= now

    bogus_pid = -42 if os.name != "nt" else 999_999_999
    assert get_process_start_time(bogus_pid) == 0


def test_current_process_start_time_consistency():
    assert get_current_process_start_time() == get_process_start_time(get_current_process_id())

# ---------------------------------------------------------------------------
# Deeper semantic checks
# ---------------------------------------------------------------------------


def _touch_every_page(buf: bytearray) -> None:
    """Write one byte per 4 KiB page to force physical allocation."""
    page = 4096
    for i in range(0, len(buf), page):
        buf[i] = 1


def _sleep_brief():
    time.sleep(0.1)


def test_process_is_active_lifecycle_and_start_time():
    """
    Spawn a child, verify active → finished transition and start-time plausibility.
    """
    child = mp.Process(target=_sleep_brief)
    child.start()

    # Active while running
    assert process_is_active(child.pid)

    start_ts = get_process_start_time(child.pid)
    assert 0 < start_ts <= int(time.time())

    child.join()

    # After exit, should report inactive and same start time (or 0 if PID recycled)
    assert not process_is_active(child.pid)
    # For most OSes the /proc entry disappears; expect 0 after exit or unchanged.
    pst_after = get_process_start_time(child.pid)
    assert pst_after in (0, start_ts)


def _noop():
    pass

def test_child_start_time_close_to_now():
    child = mp.Process(target=_noop)
    t0 = time.time()
    child.start()
    ts = get_process_start_time(child.pid)
    child.join()
    t1 = time.time()

    # Start-time recorded between the moments just before and after .start()
    assert t0 - 2 <= ts <= t1 + 2        # generous ±2 s guard


def test_nvidia_gpu_value_is_within_bounds():
    """
    0 ≤ unused ≤ #GPUs because each GPU can contribute at most 1.0.
    """
    gpu_count = None
    try:
        pynvml.nvmlInit()
        try:
            gpu_count = pynvml.nvmlDeviceGetCount()
        finally:
            pynvml.nvmlShutdown()
    except:
        pass

    unused = get_unused_nvidia_gpus()
    if gpu_count is None:
        assert unused == 0
    else:
        assert 0.0 <= unused <= gpu_count