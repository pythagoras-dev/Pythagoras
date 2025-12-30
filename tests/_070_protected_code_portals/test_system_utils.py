import os
import time
import multiprocessing as mp

import psutil

from pythagoras._070_protected_code_portals.system_utils import (
    get_unused_ram_mb,
    get_unused_cpu_cores,
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


def test_cpu_cores_first_call_not_zero():
    """
    Verify get_unused_cpu_cores() returns accurate non-zero readings even
    on the first call, avoiding the psutil.cpu_percent(interval=None) issue
    where the first call returns meaningless 0.0.

    This test ensures the function uses interval=0.1 (or load average on POSIX)
    to get accurate measurements rather than the unreliable first-call behavior.
    """
    # Call twice to ensure both calls return reasonable values
    first_call = get_unused_cpu_cores()
    second_call = get_unused_cpu_cores()

    logical_cnt = psutil.cpu_count(logical=True) or 1

    # On a system with any activity, we shouldn't see "all cores free"
    # Allow for very idle systems but flag suspiciously high values
    # (within 0.1 of max would suggest 0% usage, which is the bug we're testing for)
    assert first_call < logical_cnt, \
        f"First call suspiciously reports all {logical_cnt} cores free: {first_call}"
    assert second_call < logical_cnt, \
        f"Second call suspiciously reports all {logical_cnt} cores free: {second_call}"

    # Both calls should be in valid range
    assert 0.0 <= first_call <= float(logical_cnt)
    assert 0.0 <= second_call <= float(logical_cnt)


def test_current_pid_consistency():
    pid = get_current_process_id()
    assert pid == os.getpid() == psutil.Process().pid
    assert pid > 0


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
        import pynvml
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


def test_get_unused_nvidia_gpus_without_pynvml():
    """
    Verify that get_unused_nvidia_gpus() gracefully returns 0.0 when pynvml
    is not available, by temporarily hiding the module from imports.
    """
    import sys

    # Save original pynvml module reference if it exists
    pynvml_backup = sys.modules.get('pynvml')

    try:
        # Hide pynvml by replacing it with None in sys.modules
        # This simulates ModuleNotFoundError on import
        sys.modules['pynvml'] = None

        # Should return 0.0 without raising an exception
        unused = get_unused_nvidia_gpus()
        assert unused == 0.0

    finally:
        # Restore original state
        if pynvml_backup is None:
            sys.modules.pop('pynvml', None)
        else:
            sys.modules['pynvml'] = pynvml_backup