from persidict import PersiDict

from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._220_data_portals import DataPortal

def test_empty_data_portal(tmpdir):
    with _PortalTester(DataPortal, tmpdir) as p:
        assert isinstance(p.portal._root_dict, PersiDict)
        # assert len(p.portal._all_portals) == 1
        # assert len(p.portal._entered_portals_stack) == 1
        # assert len(p.portal._entered_portals_counters_stack) == 1

        # DataPortal now inherits from BasicPortal, not OrdinaryCodePortal
        # So it has linked_objects, not specifically linked_functions
        assert p.portal.count_linked_objects() == 0

        assert len(p.portal.global_value_store) == 0