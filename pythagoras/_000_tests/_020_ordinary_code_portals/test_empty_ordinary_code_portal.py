from persidict import PersiDict

from pythagoras import OrdinaryCodePortal
from pythagoras._010_basic_portals.portal_tester import _PortalTester

def test_empty_ordinary_code_portal(tmpdir):
    with _PortalTester(OrdinaryCodePortal, tmpdir) as p:
        assert isinstance(p.portal._root_dict, PersiDict)
        assert len(p.portal._all_portals) == 1
        assert len(p.portal._entered_portals_stack) == 1
        assert len(p.portal._entered_portals_counters_stack) == 1

