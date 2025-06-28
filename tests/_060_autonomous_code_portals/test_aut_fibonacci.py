
from pythagoras._010_basic_portals.portal_tester import _PortalTester
import pytest
from pythagoras._060_autonomous_code_portals import *


def fibonacci(n: int) -> int:
    if n in [0, 1]:
        return n
    else:
        return fibonacci(n=n-1) + fibonacci(n=n-2)

@pytest.mark.parametrize("p",[0,0.5,1])
def test_aut_fibonacci(tmpdir,p):
    with _PortalTester(
            AutonomousCodePortal
            , root_dict=tmpdir
            , p_consistency_checks=p
            ) as t:
        global fibonacci
        fibonacci_a = autonomous()(fibonacci)
        assert fibonacci_a(n=10) == 55