import pytest

from src.pythagoras import BasicPortal, _PortalTester
from src.pythagoras._010_basic_portals.basic_portal_core_classes_NEW import (
    active_portal
    , number_of_known_portals
    , number_of_active_portals
    , most_recently_created_portal
    , depth_of_active_portal_stack)


def test_portal_tester_no_params(tmpdir):
    portal1 = BasicPortal(tmpdir)
    portal1.__enter__()
    with _PortalTester():
        assert number_of_known_portals() == 0
        assert number_of_active_portals() == 0
        assert most_recently_created_portal() is None
        assert depth_of_active_portal_stack() == 0
        portal2 = BasicPortal(tmpdir)
        portal2.__enter__()
        assert number_of_active_portals() == 1
        assert active_portal() == portal2
        assert most_recently_created_portal() == portal2
        assert depth_of_active_portal_stack() == 1
        portal2.__exit__(None, None, None)
        assert most_recently_created_portal() is portal2
    assert number_of_known_portals() == 0
    assert number_of_active_portals() == 0
    assert most_recently_created_portal() is None
    assert depth_of_active_portal_stack() == 0

def test_portal_tester_with_params(tmpdir):
    portal1 = BasicPortal(tmpdir)
    portal1.__enter__()
    with _PortalTester(BasicPortal, tmpdir) as portal_tester:
        assert isinstance(most_recently_created_portal(), BasicPortal)
        assert number_of_active_portals() == 1
        assert number_of_known_portals() == 1
        assert depth_of_active_portal_stack() == 1
        portal2 = portal_tester.portal
        portal2.__enter__()
        assert number_of_active_portals() == 1
        assert depth_of_active_portal_stack() == 2
        portal2.__exit__(None, None, None)
    assert most_recently_created_portal() is None
    assert number_of_active_portals() == 0
    assert number_of_known_portals() == 0
    assert depth_of_active_portal_stack() == 0

def test_nested_portal_testers(tmpdir):
    with _PortalTester(BasicPortal, tmpdir) as t1:
        with pytest.raises(Exception):
            with _PortalTester(BasicPortal, tmpdir) as t2:
                assert t1 != t2
