"""Tests for descendant_process_info module.

Tests the process tracking utilities that identify and manage descendant
processes in the swarm, ensuring correct lifecycle management even when
process IDs are reused by the operating system.
"""

import pytest
import time
from pythagoras import get_current_process_id, get_current_process_start_time
from pythagoras._410_swarming_portals.descendant_process_info import (
    process_is_alive,
    DescendantProcessInfo,
    min_valid_process_start_time
)


# Tests for process_is_alive() function

def test_process_is_alive_with_current_process():
    """Verify current process is detected as alive."""
    pid = get_current_process_id()
    start_time = get_current_process_start_time()
    assert process_is_alive(pid, start_time) is True


def test_process_is_alive_with_wrong_timestamp():
    """Verify process not detected as alive when timestamp mismatches."""
    pid = get_current_process_id()
    wrong_timestamp = int(time.time()) - 3600  # 1 hour ago
    assert process_is_alive(pid, wrong_timestamp) is False


def test_process_is_alive_with_nonexistent_pid():
    """Verify non-existent PID is not detected as alive."""
    fake_pid = 999_999_999
    valid_timestamp = int(time.time())
    assert process_is_alive(fake_pid, valid_timestamp) is False


def test_process_is_alive_rejects_non_int_pid():
    """Verify TypeError when PID is not an integer."""
    with pytest.raises(TypeError, match="process_id must be an integer"):
        process_is_alive("12345", int(time.time()))


def test_process_is_alive_rejects_negative_pid():
    """Verify ValueError when PID is negative."""
    with pytest.raises(ValueError, match="process_id must be positive"):
        process_is_alive(-1, int(time.time()))


def test_process_is_alive_rejects_zero_pid():
    """Verify ValueError when PID is zero."""
    with pytest.raises(ValueError, match="process_id must be positive"):
        process_is_alive(0, int(time.time()))


def test_process_is_alive_rejects_non_int_timestamp():
    """Verify TypeError when timestamp is not an integer."""
    with pytest.raises(TypeError, match="process_start_time must be an integer"):
        process_is_alive(12345, "1735689600")


def test_process_is_alive_returns_false_for_old_timestamp():
    """Verify old timestamp returns False instead of raising."""
    old_timestamp = min_valid_process_start_time() - 1
    assert process_is_alive(12345, old_timestamp) is False


# Tests for DescendantProcessInfo class

def test_descendant_process_info_valid_construction():
    """Verify DescendantProcessInfo can be constructed with valid data."""
    pid = get_current_process_id()
    start_time = get_current_process_start_time()

    info = DescendantProcessInfo(
        process_id=pid,
        process_start_time=start_time,
        ancestor_process_id=pid,
        ancestor_process_start_time=start_time,
        process_type="test_worker"
    )

    assert info.process_id == pid
    assert info.process_start_time == start_time
    assert info.ancestor_process_id == pid
    assert info.ancestor_process_start_time == start_time
    assert info.process_type == "test_worker"


def test_descendant_process_info_is_alive_when_both_processes_alive():
    """Verify is_alive returns True when both descendant and ancestor are alive."""
    pid = get_current_process_id()
    start_time = get_current_process_start_time()

    info = DescendantProcessInfo(
        process_id=pid,
        process_start_time=start_time,
        ancestor_process_id=pid,
        ancestor_process_start_time=start_time,
        process_type="test_worker"
    )

    assert info.is_alive() is True


def test_descendant_process_info_is_alive_when_descendant_dead():
    """Verify is_alive returns False when descendant process doesn't exist."""
    pid = get_current_process_id()
    start_time = get_current_process_start_time()

    info = DescendantProcessInfo(
        process_id=999_999_999,  # Non-existent PID
        process_start_time=start_time,
        ancestor_process_id=pid,
        ancestor_process_start_time=start_time,
        process_type="test_worker"
    )

    assert info.is_alive() is False


def test_descendant_process_info_is_alive_when_ancestor_dead():
    """Verify is_alive returns False when ancestor process doesn't exist."""
    pid = get_current_process_id()
    start_time = get_current_process_start_time()

    info = DescendantProcessInfo(
        process_id=pid,
        process_start_time=start_time,
        ancestor_process_id=999_999_999,  # Non-existent PID
        ancestor_process_start_time=start_time,
        process_type="test_worker"
    )

    assert info.is_alive() is False


def test_descendant_process_info_terminate_rejects_negative_timeout():
    """Verify terminate() raises ValueError for negative timeout."""
    pid = get_current_process_id()
    start_time = get_current_process_start_time()

    info = DescendantProcessInfo(
        process_id=pid,
        process_start_time=start_time,
        ancestor_process_id=pid,
        ancestor_process_start_time=start_time,
        process_type="test_worker"
    )

    with pytest.raises(ValueError, match="timeout must be non-negative"):
        info.terminate(timeout=-1)


def test_descendant_process_info_terminate_on_dead_process_is_safe():
    """Verify terminate() safely handles already-dead process."""
    pid = get_current_process_id()
    start_time = get_current_process_start_time()

    info = DescendantProcessInfo(
        process_id=999_999_999,  # Non-existent PID
        process_start_time=start_time,
        ancestor_process_id=pid,
        ancestor_process_start_time=start_time,
        process_type="test_worker"
    )

    # Should not raise, just returns safely
    info.terminate(timeout=1)


# Constructor validation tests - process_id

def test_descendant_process_info_rejects_non_int_process_id():
    """Verify TypeError when process_id is not an integer."""
    with pytest.raises(TypeError, match="process_id must be an integer"):
        DescendantProcessInfo(
            process_id="12345",
            process_start_time=int(time.time()),
            ancestor_process_id=100,
            ancestor_process_start_time=int(time.time()),
            process_type="test"
        )


def test_descendant_process_info_rejects_negative_process_id():
    """Verify ValueError when process_id is negative."""
    with pytest.raises(ValueError, match="process_id must be positive"):
        DescendantProcessInfo(
            process_id=-1,
            process_start_time=int(time.time()),
            ancestor_process_id=100,
            ancestor_process_start_time=int(time.time()),
            process_type="test"
        )


def test_descendant_process_info_rejects_zero_process_id():
    """Verify ValueError when process_id is zero."""
    with pytest.raises(ValueError, match="process_id must be positive"):
        DescendantProcessInfo(
            process_id=0,
            process_start_time=int(time.time()),
            ancestor_process_id=100,
            ancestor_process_start_time=int(time.time()),
            process_type="test"
        )


# Constructor validation tests - process_start_time

def test_descendant_process_info_rejects_non_int_process_start_time():
    """Verify TypeError when process_start_time is not an integer."""
    with pytest.raises(TypeError, match="process_start_time must be an integer"):
        DescendantProcessInfo(
            process_id=12345,
            process_start_time="1735689600",
            ancestor_process_id=100,
            ancestor_process_start_time=int(time.time()),
            process_type="test"
        )


def test_descendant_process_info_rejects_old_process_start_time():
    """Verify ValueError when process_start_time is outside boot-time window."""
    with pytest.raises(ValueError, match="boot-time window"):
        DescendantProcessInfo(
            process_id=12345,
            process_start_time=min_valid_process_start_time() - 1,
            ancestor_process_id=100,
            ancestor_process_start_time=int(time.time()),
            process_type="test"
        )


# Constructor validation tests - ancestor_process_id

def test_descendant_process_info_rejects_non_int_ancestor_process_id():
    """Verify TypeError when ancestor_process_id is not an integer."""
    with pytest.raises(TypeError, match="ancestor_process_id must be an integer"):
        DescendantProcessInfo(
            process_id=12345,
            process_start_time=int(time.time()),
            ancestor_process_id="100",
            ancestor_process_start_time=int(time.time()),
            process_type="test"
        )


def test_descendant_process_info_rejects_negative_ancestor_process_id():
    """Verify ValueError when ancestor_process_id is negative."""
    with pytest.raises(ValueError, match="ancestor_process_id must be positive"):
        DescendantProcessInfo(
            process_id=12345,
            process_start_time=int(time.time()),
            ancestor_process_id=-1,
            ancestor_process_start_time=int(time.time()),
            process_type="test"
        )


def test_descendant_process_info_rejects_zero_ancestor_process_id():
    """Verify ValueError when ancestor_process_id is zero."""
    with pytest.raises(ValueError, match="ancestor_process_id must be positive"):
        DescendantProcessInfo(
            process_id=12345,
            process_start_time=int(time.time()),
            ancestor_process_id=0,
            ancestor_process_start_time=int(time.time()),
            process_type="test"
        )


# Constructor validation tests - ancestor_process_start_time

def test_descendant_process_info_rejects_non_int_ancestor_start_time():
    """Verify TypeError when ancestor_process_start_time is not an integer."""
    with pytest.raises(TypeError, match="ancestor_process_start_time must be an integer"):
        DescendantProcessInfo(
            process_id=12345,
            process_start_time=int(time.time()),
            ancestor_process_id=100,
            ancestor_process_start_time="1735689600",
            process_type="test"
        )


def test_descendant_process_info_rejects_old_ancestor_start_time():
    """Verify ValueError when ancestor_process_start_time is outside boot-time window."""
    with pytest.raises(ValueError, match="boot-time window"):
        DescendantProcessInfo(
            process_id=12345,
            process_start_time=int(time.time()),
            ancestor_process_id=100,
            ancestor_process_start_time=min_valid_process_start_time() - 1,
            process_type="test"
        )


# Constructor validation tests - process_type

def test_descendant_process_info_rejects_non_string_process_type():
    """Verify TypeError when process_type is not a string."""
    with pytest.raises(TypeError, match="process_type must be a string"):
        DescendantProcessInfo(
            process_id=12345,
            process_start_time=int(time.time()),
            ancestor_process_id=100,
            ancestor_process_start_time=int(time.time()),
            process_type=123
        )


def test_descendant_process_info_rejects_empty_process_type():
    """Verify ValueError when process_type is empty string."""
    with pytest.raises(ValueError, match="process_type cannot be empty"):
        DescendantProcessInfo(
            process_id=12345,
            process_start_time=int(time.time()),
            ancestor_process_id=100,
            ancestor_process_start_time=int(time.time()),
            process_type=""
        )
