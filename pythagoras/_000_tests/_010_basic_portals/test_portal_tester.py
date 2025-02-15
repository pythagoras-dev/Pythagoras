import pytest

from pythagoras import BasicPortal, _PortalTester, DataPortal
from pythagoras._010_basic_portals.portal_aware_classes import (
    _noncurrent_portals, _most_recently_entered_portal, _entered_portals)


def test_portal_tester_no_params(tmpdir):
    portal1 = BasicPortal(tmpdir)
    portal1.__enter__()
    with _PortalTester():
        assert _most_recently_entered_portal() == None
        assert len(_noncurrent_portals()) == 0
        assert len(_entered_portals()) == 0
        portal2 = BasicPortal(tmpdir)
        portal2.__enter__()
        portal2.__exit__(None, None, None)
    assert _most_recently_entered_portal() == None
    assert len(_noncurrent_portals()) == 0
    assert len(_entered_portals()) == 0

def test_portal_tester_with_params(tmpdir):
    portal1 = BasicPortal(tmpdir)
    portal1.__enter__()
    with _PortalTester(BasicPortal, tmpdir):
        assert isinstance(_most_recently_entered_portal(), BasicPortal)
        assert len(_noncurrent_portals()) == 0
        assert len(_entered_portals()) == 1
        portal2 = BasicPortal(tmpdir)
        portal2.__enter__()
        portal2.__exit__(None, None, None)
    assert _most_recently_entered_portal() == None
    assert len(_noncurrent_portals()) == 0
    assert len(_entered_portals()) == 0

def test_nested_portal_testers(tmpdir):
    with _PortalTester(BasicPortal, tmpdir) as t1:
        with pytest.raises(Exception):
            with _PortalTester(BasicPortal, tmpdir) as t2:
                assert t1 != t2
