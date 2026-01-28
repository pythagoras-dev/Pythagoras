"""Tests for BasicPortal core functionality."""
from pythagoras._210_basic_portals import *
from pythagoras._210_basic_portals import _PortalTester
from pythagoras._210_basic_portals.basic_portal_core_classes import (
    _clear_all_portals, MAX_NESTED_PORTALS
)
import pytest


def test_portal(tmpdir):
    """Verify basic portal creation, registration, and activation."""
    with _PortalTester():

        portal = BasicPortal(tmpdir.mkdir("awer"))
        assert portal is not None
        assert get_most_recently_created_portal() is portal
        assert count_known_portals() == 1
        assert count_active_portals() == 0
        assert measure_active_portals_stack() == 0
        assert count_linked_portal_aware_objects() == 0

        assert get_current_portal() is portal

        assert count_known_portals() == 1
        assert count_active_portals() == 1
        assert measure_active_portals_stack() == 1

        _portal2 = BasicPortal(tmpdir.mkdir("awasder"))
        portal3 = BasicPortal(tmpdir.mkdir("aadfgggr"))

        assert get_current_portal() is portal
        assert get_most_recently_created_portal() is portal3
        assert count_known_portals() == 3
        assert count_active_portals() == 1
        assert measure_active_portals_stack() == 1
        assert count_linked_portal_aware_objects() == 0



def test_clear_all_portals(tmpdir):
    """Verify _clear_all_portals resets all portal state."""
    with _PortalTester():
        _portal = BasicPortal(tmpdir)
        _portal2 = BasicPortal(tmpdir)
        _portal3 = BasicPortal(tmpdir)
        _clear_all_portals()
        assert get_most_recently_created_portal() is None
        assert count_known_portals() == 0
        assert count_active_portals() == 0
        assert measure_active_portals_stack() == 0
        assert count_linked_portal_aware_objects() == 0



def test_portal_nested(tmpdir):
    """Verify nested portal contexts track active/current state correctly."""
    with _PortalTester():

        portal = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))
        portal3 = BasicPortal(tmpdir.mkdir("p3"))

        assert get_most_recently_created_portal() is portal3

        with portal:
            assert get_current_portal() == portal
            assert count_active_portals() == 1
            assert measure_active_portals_stack() == 1
            assert count_linked_portal_aware_objects() == 0
            with portal2:
                assert get_current_portal() == portal2
                assert count_active_portals() == 2
                assert measure_active_portals_stack() == 2
                assert count_linked_portal_aware_objects() == 0
                with portal3:
                    assert get_current_portal() == portal3
                    assert count_active_portals() == 3
                    assert measure_active_portals_stack() == 3
                    assert count_linked_portal_aware_objects() == 0
                    with portal2:
                        assert get_current_portal() == portal2
                        assert count_active_portals() == 3
                        assert measure_active_portals_stack() == 4
                        assert count_linked_portal_aware_objects() == 0
                        assert get_most_recently_created_portal() is portal3
                    assert get_current_portal() == portal3
                    assert count_active_portals() == 3
                    assert measure_active_portals_stack() == 3
                    assert count_linked_portal_aware_objects() == 0
                assert get_current_portal() == portal2
                assert count_active_portals() == 2
                assert measure_active_portals_stack() == 2
                assert count_linked_portal_aware_objects() == 0
            assert get_current_portal() == portal
            assert count_active_portals() == 1
            assert measure_active_portals_stack() == 1
            assert count_linked_portal_aware_objects() == 0


def test_get_nonactive_portals(tmpdir):
    """Test get_nonactive_portals returns portals not in active stack."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))
        portal3 = BasicPortal(tmpdir.mkdir("p3"))

        # No portals active initially
        nonactive = get_nonactive_portals()
        assert len(nonactive) == 3
        assert portal1 in nonactive
        assert portal2 in nonactive
        assert portal3 in nonactive

        # Activate portal1
        with portal1:
            nonactive = get_nonactive_portals()
            assert len(nonactive) == 2
            assert portal1 not in nonactive
            assert portal2 in nonactive
            assert portal3 in nonactive

            # Activate portal2 as well
            with portal2:
                nonactive = get_nonactive_portals()
                assert len(nonactive) == 1
                assert portal1 not in nonactive
                assert portal2 not in nonactive
                assert portal3 in nonactive

        # Back to no active portals
        nonactive = get_nonactive_portals()
        assert len(nonactive) == 3


def test_portal_is_current(tmpdir):
    """Test portal.is_current property tracks current portal status."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        # No portals active - neither is current
        assert not portal1.is_current
        assert not portal2.is_current

        # Activate portal1 - it becomes current
        with portal1:
            assert portal1.is_current
            assert not portal2.is_current

            # Activate portal2 nested - it becomes current
            with portal2:
                assert not portal1.is_current
                assert portal2.is_current

            # Back to portal1 context
            assert portal1.is_current
            assert not portal2.is_current


def test_portal_is_active(tmpdir):
    """Test portal.is_active property tracks active portal stack."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        # No portals active initially
        assert not portal1.is_active
        assert not portal2.is_active

        # Activate portal1
        with portal1:
            assert portal1.is_active
            assert not portal2.is_active

            # Activate portal2 nested - both active
            with portal2:
                assert portal1.is_active
                assert portal2.is_active

            # Back to portal1 context - only portal1 active
            assert portal1.is_active
            assert not portal2.is_active

        # No portals active
        assert not portal1.is_active
        assert not portal2.is_active


def test_portal_identity_key_stability(tmpdir):
    """Test portal identity_key is stable and deterministic."""
    with _PortalTester():
        portal = BasicPortal(tmpdir.mkdir("p1"))

        # Identity key should be stable across multiple accesses
        ik1 = portal.identity_key
        ik2 = portal.identity_key
        assert ik1 == ik2


def test_portal_identity_key_uniqueness(tmpdir):
    """Test different portals have different identity keys."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        # Different portals should have different identity keys
        assert portal1.identity_key != portal2.identity_key


def test_portal_identity_key_deterministic(tmpdir):
    """Test portal identity_key is deterministic for same parameters."""
    with _PortalTester():
        dir1 = tmpdir.mkdir("same_dir")
        portal1 = BasicPortal(dir1)
        ik1 = portal1.identity_key

        _clear_all_portals()

        # Create portal with same parameters
        portal2 = BasicPortal(dir1)
        ik2 = portal2.identity_key

        # Should have the same identity key
        assert ik1 == ik2


def test_portal_max_nesting_limit(tmpdir):
    """Test that exceeding MAX_NESTED_PORTALS raises RuntimeError."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        # Create a context manager chain that exceeds the limit
        with pytest.raises(RuntimeError):
            for _ in range(MAX_NESTED_PORTALS + 1):
                portal.__enter__()


def test_portal_pop_wrong_portal_error(tmpdir):
    """Test that popping wrong portal from stack raises RuntimeError."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        with portal1:
            # Try to pop portal2 which is not on stack
            with pytest.raises(RuntimeError):
                portal2.__exit__(None, None, None)


def test_portal_entropy_infuser_error_after_clear(tmpdir):
    """Test that accessing entropy_infuser after _clear() raises RuntimeError."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        # Should work normally
        _ = portal.entropy_infuser

        # Clear the portal
        portal._clear()

        # Now accessing entropy_infuser should raise
        with pytest.raises(RuntimeError):
            _ = portal.entropy_infuser
