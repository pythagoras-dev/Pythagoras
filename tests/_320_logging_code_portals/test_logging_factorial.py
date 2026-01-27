
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._320_logging_code_portals import *


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

def test_logging_factorial(tmpdir):
    with _PortalTester(LoggingCodePortal
            , root_dict=tmpdir):
        global factorial
        new_factorial = logging()(factorial)
        assert new_factorial(n=5) == 120