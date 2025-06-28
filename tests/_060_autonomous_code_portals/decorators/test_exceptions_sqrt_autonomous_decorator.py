import pytest

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._800_signatures_and_converters.current_date_gmt_str import current_date_gmt_string
from pythagoras._060_autonomous_code_portals import *



def test_sqrt(tmpdir):
    # tmpdir = "TEST_SQRT_"*3+str(time.time())
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:

        @autonomous()
        def my_sqrt(x: float) -> float:
            from math import sqrt
            return sqrt(x)

        date_str_1 = current_date_gmt_string()

        n = 5
        for i in range(-10, n):
            if i <= 0:
                my_sqrt(x=-i)
                continue
            with pytest.raises(ValueError):
                my_sqrt(x=-i)

        assert len(t.portal._crash_history) == n-1
