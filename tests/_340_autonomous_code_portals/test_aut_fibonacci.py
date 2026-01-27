
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._340_autonomous_code_portals import *


def fibonacci(n: int) -> int:
    if n in [0, 1]:
        return n
    else:
        return fibonacci(n=n-1) + fibonacci(n=n-2)

def test_aut_fibonacci(tmpdir):
    with _PortalTester(
            AutonomousCodePortal
            , root_dict=tmpdir
            
            ):
        global fibonacci
        fibonacci_a = autonomous()(fibonacci)
        assert fibonacci_a(n=10) == 55