from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure

import pythagoras as pth


def fibonacci(n: int) -> int:
    if n in [0, 1]:
        return n
    else:
        return fibonacci(n=n-1) + fibonacci(n=n-2)

def factorial(n: int) -> int:
    if n == 0:
        return 1
    else:
        return n * factorial(n=n-1)

def do_nothing(x: int) -> int:
    return x

def always_OK(**kwargs):
    return pth.VALIDATION_SUCCESSFUL


def test_pure_portals_smoke_test(tmpdir):
    # tmpdir = "YIYIYIYIYIYIYIYIYIYIYIYIYIYIYIYIY"
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal
        global fibonacci,factorial,do_nothing
        fibonacci_p = pure(portal=portal)(fibonacci)
        _factorial_p = pure(portal=portal)(factorial)
        do_nothing_p = pure(portal=portal)(do_nothing)

        # Lazy registration - not registered until portal accessed
        assert portal.get_number_of_linked_functions() == 0
        # Trigger registration via portal access
        _ = fibonacci_p.portal
        _ = _factorial_p.portal
        _ = do_nothing_p.portal
        assert portal.get_number_of_linked_functions() == 3

        assert fibonacci_p(n=4) == 3
        assert _factorial_p(n=4) == 24
        assert do_nothing_p(x=4) == 4
        assert portal.get_number_of_linked_functions() == 3


        def func_increment(x: int) -> int:
            return x + 1

        func_increment_p = pure()(func_increment)
        assert portal.get_number_of_linked_functions() == 3
        assert func_increment_p(x=4) == 5
        assert portal.get_number_of_linked_functions() == 3


def test_pure_portals_execution_results(tmpdir):
    # tmpdir = "YIYIYIYIYIYIYIYIYIYIYIYIYIYIYIYIY"
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal
        global fibonacci,factorial,do_nothing
        fibonacci_p = pure()(fibonacci)
        _factorial_p = pure()(factorial)
        do_nothing_p = pure()(do_nothing)

        assert len(portal._execution_results) == 0
        assert do_nothing_p(x=4) == 4
        assert len(portal._execution_results) == 1

        assert fibonacci_p(n=4) == 3
        assert len(portal._execution_results) == 6


def test_pure_portals_execution_requests(tmpdir):
    # tmpdir = "YIYIYIYIYIYIYIYIYIYIYIYIYIYIYIYIY"
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal
        global fibonacci, factorial, do_nothing
        fibonacci_p = pure()(fibonacci)
        _factorial_p = pure()(factorial)
        do_nothing_p = pure()(do_nothing)

        assert len(portal._execution_requests) == 0
        assert do_nothing_p(x=4) == 4
        assert len(portal._execution_requests) == 0
        assert fibonacci_p(n=4) == 3
        assert len(portal._execution_requests) == 0



def test_pure_portals_always_OK(tmpdir):
    # tmpdir = "YIYIYIYIYIYIYIYIYIYIYIYIYIYIYIYIY"
    with _PortalTester(PureCodePortal, tmpdir):
        global fibonacci,factorial,do_nothing
        fibonacci_p = pure(pre_validators=[always_OK])(fibonacci)

        assert fibonacci_p(n=4) == 3
