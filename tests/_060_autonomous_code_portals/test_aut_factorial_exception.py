from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._060_autonomous_code_portals import *


def factorial(n:int) -> int:
    if n in [0, 1]:
        raise ValueError("Factorial is not defined for 0 or 1.")
    else:
        return n * factorial(n=n-1)

def test_aut_factorial(tmpdir):
    # tmpdir = 20*"Q"+str(int(time.time()))
    try:
        with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:
            crash_history = t.portal._crash_history
            global factorial
            factorial = autonomous()(factorial)
            assert factorial(n=5) == 120
    except:
        assert len(crash_history) == 1
