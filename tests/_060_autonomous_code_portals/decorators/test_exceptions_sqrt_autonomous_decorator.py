import pytest

from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._820_strings_signatures_converters.current_date_gmt_str import current_date_gmt_string
from src.pythagoras._060_autonomous_code_portals import *



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

        assert len(t.portal.crash_history) == n-1
