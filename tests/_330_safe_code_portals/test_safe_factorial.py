
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._330_safe_code_portals import *


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

def test_safe_factorial(tmpdir):
    with _PortalTester(SafeCodePortal
            , root_dict=tmpdir):
        new_factorial = safe()(factorial)
        assert new_factorial(n=5) == 120