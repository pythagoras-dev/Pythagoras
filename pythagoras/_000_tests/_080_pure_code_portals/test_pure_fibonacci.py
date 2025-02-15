from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._080_pure_code_portals.pure_decorator import pure


def fibonacci(n: int) -> int:
    if n in [0, 1]:
        return n
    else:
        return fibonacci(n=n-1) + fibonacci(n=n-2)

def test_pure_fibonacci(tmpdir):
    # tmpdir = "YIYIYIYIYIYIYIYIYIYIYIYIYIYIYIYIY"
    with _PortalTester(PureCodePortal, tmpdir):
        global fibonacci
        fibonacci = pure()(fibonacci)
        assert fibonacci(n=50) == 12586269025
        assert fibonacci(n=50) == 12586269025