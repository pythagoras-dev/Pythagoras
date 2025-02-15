import pytest
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._820_strings_signatures_converters.current_date_gmt_str import current_date_gmt_string
from pythagoras._060_autonomous_code_portals import *



def test_zero_div(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:

        date_str_1 = current_date_gmt_string()

        @autonomous()
        def zero_div(x:float)->float:
            return x/0

        with pytest.raises(ZeroDivisionError):
            zero_div(x=2024)

        date_str_2 = current_date_gmt_string()

        assert len(t.portal.crash_history) == 1
        for event_id  in list(t.portal.crash_history):
            # assert "ZeroDivisionError" in event_id[1]
            # assert "zero_div" in event_id[1]
            # assert event_id[0] in [date_str_1, date_str_2]
            pass
