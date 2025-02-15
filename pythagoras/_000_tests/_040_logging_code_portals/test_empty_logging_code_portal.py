from persidict import PersiDict

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._040_logging_code_portals import (
    LoggingCodePortal)

def test_empty_logging_code_portal(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        assert isinstance(p.portal._root_dict, PersiDict)
        assert len(p.portal._all_portals) == 1
        assert len(p.portal._entered_portals_stack) == 1
        assert len(p.portal._entered_portals_counters_stack) == 1

        assert len(p.portal.known_functions) == 0

        assert len(p.portal.value_store) == 0
        pcc = p.portal._p_consistency_checks
        assert 0 <= pcc <= 1

        assert len(p.portal.crash_history) == 0
        assert len(p.portal.event_history) == 0

        assert  len(p.portal.run_history.py) == 0
        assert len(p.portal.run_history.pkl) == 0
        assert len(p.portal.run_history.txt) == 0
        assert len(p.portal.run_history.json) == 0