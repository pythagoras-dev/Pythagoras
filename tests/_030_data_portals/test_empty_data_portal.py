from persidict import PersiDict

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._030_data_portals import DataPortal

def test_empty_data_portal(tmpdir):
    with _PortalTester(DataPortal, tmpdir) as p:
        assert isinstance(p.portal._root_dict, PersiDict)
        # assert len(p.portal._all_portals) == 1
        # assert len(p.portal._entered_portals_stack) == 1
        # assert len(p.portal._entered_portals_counters_stack) == 1

        assert p.portal.get_number_of_linked_functions() == 0

        assert len(p.portal._value_store) == 0
        pcc = p.portal.p_consistency_checks
        assert 0 <= pcc <= 1