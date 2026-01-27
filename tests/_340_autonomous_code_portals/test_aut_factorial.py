
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._340_autonomous_code_portals import *


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

def test_aut_factorial(tmpdir):
    with _PortalTester(AutonomousCodePortal
            , root_dict=tmpdir):
        global factorial
        factorial_new = autonomous(excessive_logging=True)(factorial)
        assert factorial_new(n=5) == 120