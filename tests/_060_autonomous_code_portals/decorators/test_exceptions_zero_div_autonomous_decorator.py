import pytest
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._060_autonomous_code_portals import *



def test_zero_div(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:

        @autonomous()
        def zero_div(x:float)->float:
            return x/0

        with pytest.raises(ZeroDivisionError):
            zero_div(x=2024)


        assert len(t.portal._crash_history) == 1

