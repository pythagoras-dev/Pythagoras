from persidict import PersiDict

from pythagoras._010_basic_portals import (
    get_number_of_portals_in_active_stack
    , get_depth_of_active_portal_stack
    , get_active_portal
    , _PortalTester)
from pythagoras._040_logging_code_portals import (
    LoggingCodePortal)

def test_empty_logging_code_portal(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        assert isinstance(p.portal._root_dict, PersiDict)
        assert get_number_of_portals_in_active_stack() == 1
        assert get_depth_of_active_portal_stack() == 1
        assert get_active_portal() is p.portal

        assert p.portal.get_number_of_linked_functions() == 0

        assert len(p.portal._value_store) == 0
        pcc = p.portal.p_consistency_checks
        assert 0 <= pcc <= 1

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 0
        assert len(p.portal._run_history.pkl) == 0
        assert len(p.portal._run_history.txt) == 0
        assert len(p.portal._run_history.json) == 0