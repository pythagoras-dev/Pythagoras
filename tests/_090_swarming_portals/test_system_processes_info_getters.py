import os
import time
import multiprocessing as mp

import psutil

from pythagoras import (get_current_process_id, get_current_process_start_time,
                        get_process_start_time)


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
