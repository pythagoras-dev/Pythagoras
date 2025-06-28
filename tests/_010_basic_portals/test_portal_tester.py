import pytest

from pythagoras import BasicPortal, _PortalTester
from pythagoras._010_basic_portals.basic_portal_core_classes import (
    get_active_portal
    , get_number_of_known_portals
    , get_number_of_portals_in_active_stack
    , get_most_recently_created_portal
    , get_depth_of_active_portal_stack)


def test_portal_tester_no_params(tmpdir):
    portal1 = BasicPortal(tmpdir)
    portal1.__enter__()
    with _PortalTester():
        assert get_number_of_known_portals() == 0
        assert get_number_of_portals_in_active_stack() == 0
        assert get_most_recently_created_portal() is None
        assert get_depth_of_active_portal_stack() == 0
        portal2 = BasicPortal(tmpdir)
        portal2.__enter__()
        assert get_number_of_portals_in_active_stack() == 1
        assert get_active_portal() == portal2
        assert get_most_recently_created_portal() == portal2
        assert get_depth_of_active_portal_stack() == 1
        portal2.__exit__(None, None, None)
        assert get_most_recently_created_portal() is portal2
    assert get_number_of_known_portals() == 0
    assert get_number_of_portals_in_active_stack() == 0
    assert get_most_recently_created_portal() is None
    assert get_depth_of_active_portal_stack() == 0

def test_portal_tester_with_params(tmpdir):
    portal1 = BasicPortal(tmpdir)
    portal1.__enter__()
    with _PortalTester(BasicPortal, tmpdir) as portal_tester:
        assert isinstance(get_most_recently_created_portal(), BasicPortal)
        assert get_number_of_portals_in_active_stack() == 1
        assert get_number_of_known_portals() == 1
        assert get_depth_of_active_portal_stack() == 1
        portal2 = portal_tester.portal
        portal2.__enter__()
        assert get_number_of_portals_in_active_stack() == 1
        assert get_depth_of_active_portal_stack() == 2
        portal2.__exit__(None, None, None)
    assert get_most_recently_created_portal() is None
    assert get_number_of_portals_in_active_stack() == 0
    assert get_number_of_known_portals() == 0
    assert get_depth_of_active_portal_stack() == 0

def test_nested_portal_testers(tmpdir):
    with _PortalTester(BasicPortal, tmpdir) as t1:
        with pytest.raises(Exception):
            with _PortalTester(BasicPortal, tmpdir) as t2:
                assert t1 != t2
