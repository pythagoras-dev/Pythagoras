from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFn)
from pythagoras._360_pure_code_portals.pure_decorator import pure


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

def test_pure_factorial_fn_class(tmpdir):
    # tmpdir = "TTTTTTTT-TTTTTTTT-TTTTTTTT-TTTTTTTT-TTTTTTTT-TTTTTTTT"
    with _PortalTester(PureCodePortal
            , tmpdir
            ) as t:
        # global factorial
        assert len(t.portal._crash_history) == 0
        assert len(t.portal._execution_results) == 0
        assert len(t.portal._execution_requests) == 0

        factorial_m = PureFn(factorial)
        assert factorial_m(n=5) == 120
        assert factorial_m(n=5) == 120

        assert len(t.portal._crash_history) == 0
        assert len(t.portal._execution_results) == 5
        assert len(t.portal._execution_requests) == 0

def test_pure_factorial_decorator(tmpdir):
    # tmpdir = "TTTTTTTT-TTTTTTTT-TTTTTTTT-TTTTTTTT-TTTTTTTT-TTTTTTTT-TTTTTTTT"
    with _PortalTester(PureCodePortal
            , tmpdir
            ) as t:
        # global factorial
        assert len(t.portal._crash_history) == 0
        assert len(t.portal._execution_results) == 0
        assert len(t.portal._execution_requests) == 0

        factorial_d = pure()(factorial)

        assert factorial_d(n=2) == 2
        assert factorial_d(n=3) == 6

        for i in range(10):
            assert factorial_d(n=10) == 3628800

        assert len(t.portal._crash_history) == 0
        assert len(t.portal._execution_results) == 10
        assert len(t.portal._execution_requests) == 0


