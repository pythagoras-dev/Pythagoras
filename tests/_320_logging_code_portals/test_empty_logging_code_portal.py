from persidict import PersiDict

from pythagoras._210_basic_portals import (
    count_active_portals
    , measure_active_portals_stack
    , get_current_portal
    , _PortalTester)
from pythagoras._320_logging_code_portals import (
    LoggingCodePortal)

def test_empty_logging_code_portal(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        assert isinstance(p.portal._root_dict, PersiDict)
        assert count_active_portals() == 1
        assert measure_active_portals_stack() == 1
        assert get_current_portal() is p.portal

        assert p.portal.get_number_of_linked_functions() == 0

        assert len(p.portal.global_value_store) == 0

        assert len(p.portal._crash_history) == 0
        assert len(p.portal._event_history) == 0

        assert  len(p.portal._run_history.py) == 0
        assert len(p.portal._run_history.pkl) == 0
        assert len(p.portal._run_history.txt) == 0
        assert len(p.portal._run_history.json) == 0