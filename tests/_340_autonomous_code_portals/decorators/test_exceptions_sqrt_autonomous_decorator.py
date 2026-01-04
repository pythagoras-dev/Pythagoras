import pytest

from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._340_autonomous_code_portals import *



def test_sqrt(tmpdir):
    # tmpdir = "TEST_SQRT_"*3+str(time.time())
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:

        @autonomous()
        def my_sqrt(x: float) -> float:
            from math import sqrt
            return sqrt(x)

        n = 5
        for i in range(-10, n):
            if i <= 0:
                my_sqrt(x=-i)
                continue
            with pytest.raises(ValueError):
                my_sqrt(x=-i)

        assert len(t.portal._crash_history) == n-1
