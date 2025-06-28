import pytest

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._040_logging_code_portals import *


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

@pytest.mark.parametrize("p",[0, 0.5, 1])
def test_logging_factorial(tmpdir,p):
    with _PortalTester(LoggingCodePortal
            , root_dict=tmpdir, p_consistency_checks=p):
        global factorial
        new_factorial = logging()(factorial)
        assert new_factorial(n=5) == 120