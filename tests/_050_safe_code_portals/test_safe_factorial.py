import pytest

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._050_safe_code_portals import *


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

@pytest.mark.parametrize("p",[0,0.5,1])
def test_safe_factorial(tmpdir,p):
    with _PortalTester(SafeCodePortal
            , root_dict=tmpdir, p_consistency_checks=p):
        new_factorial = safe()(factorial)
        assert new_factorial(n=5) == 120