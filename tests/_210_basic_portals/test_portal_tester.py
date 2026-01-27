"""Tests for _PortalTester context manager."""
import pytest

from pythagoras import (
    BasicPortal, _PortalTester,
    get_current_portal,
    count_known_portals,
    count_active_portals,
    get_most_recently_created_portal,
    measure_active_portals_stack
)


def test_portal_tester_no_params(tmpdir):
    """Verify _PortalTester clears and restores registry state without parameters."""
    portal1 = BasicPortal(tmpdir)
    portal1.__enter__()
    with _PortalTester():
        assert count_known_portals() == 0
        assert count_active_portals() == 0
        assert get_most_recently_created_portal() is None
        assert measure_active_portals_stack() == 0
        portal2 = BasicPortal(tmpdir)
        portal2.__enter__()
        assert count_active_portals() == 1
        assert get_current_portal() == portal2
        assert get_most_recently_created_portal() == portal2
        assert measure_active_portals_stack() == 1
        portal2.__exit__(None, None, None)
        assert get_most_recently_created_portal() is portal2
    assert count_known_portals() == 0
    assert count_active_portals() == 0
    assert get_most_recently_created_portal() is None
    assert measure_active_portals_stack() == 0

def test_portal_tester_with_params(tmpdir):
    """Verify _PortalTester creates and manages portal when given parameters."""
    portal1 = BasicPortal(tmpdir)
    portal1.__enter__()
    with _PortalTester(BasicPortal, tmpdir) as portal_tester:
        assert isinstance(get_most_recently_created_portal(), BasicPortal)
        assert count_active_portals() == 1
        assert count_known_portals() == 1
        assert measure_active_portals_stack() == 1
        portal2 = portal_tester.portal
        portal2.__enter__()
        assert count_active_portals() == 1
        assert measure_active_portals_stack() == 2
        portal2.__exit__(None, None, None)
    assert get_most_recently_created_portal() is None
    assert count_active_portals() == 0
    assert count_known_portals() == 0
    assert measure_active_portals_stack() == 0

def test_nested_portal_testers(tmpdir):
    """Verify nested _PortalTester instances raise an exception."""
    with _PortalTester(BasicPortal, tmpdir) as t1:
        with pytest.raises(Exception):
            with _PortalTester(BasicPortal, tmpdir) as t2:
                assert t1 != t2
