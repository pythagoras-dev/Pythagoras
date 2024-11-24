from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._070_pure_functions.pure_core_classes import (
    PureCodePortal,PureFnExecutionResultAddr)
from pythagoras._070_pure_functions.pure_decorator import pure



def test_run_list(tmpdir):

    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure()
        def dbl(x: float) -> float:
            return x * 2

        input = []
        for i in [0, 1, 2, 3, "test", -1, -2, -3, -4]:
            input.append(dict(x=i))


        addrs = dbl.run_list(input)
        results = [a.get() for a in addrs]
        assert results == [0, 2, 4, 6, "testtest", -2, -4, -6, -8]