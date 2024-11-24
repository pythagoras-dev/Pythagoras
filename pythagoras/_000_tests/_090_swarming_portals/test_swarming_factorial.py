from copy import deepcopy
from pythagoras import BasicPortal
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._090_swarming_portals.swarming_portals import (
    SwarmingPortal, _process_random_execution_request)
from pythagoras._070_pure_functions.pure_decorator import pure
import pythagoras as pth
import pytest


def factorial(n: int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n - 1)

def get_factorial_address(n:int, dir):
    with _PortalTester(SwarmingPortal
            , dir, n_background_workers=0) as t:
        new_factorial = pure()(factorial)
        address = new_factorial.swarm(n=n)
        address._invalidate_cache()
        return address

@pytest.mark.parametrize("p",[0, 0.5, 1])
def test_swarming_factorial(tmpdir,p):
    address = get_factorial_address(n=5, dir=tmpdir)
    with _PortalTester(SwarmingPortal
            , tmpdir
            , n_background_workers=2
            , p_consistency_checks=p) as t:
        address._portal = t.portal
        assert address.get() == 120
