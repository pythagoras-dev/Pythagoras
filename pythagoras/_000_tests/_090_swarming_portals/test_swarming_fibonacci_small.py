from copy import deepcopy
from pythagoras import BasicPortal
import time
import pytest
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._090_swarming_portals.swarming_portals import (
    SwarmingPortal, _process_random_execution_request)
from pythagoras._080_pure_code_portals.pure_decorator import pure
import pythagoras as pth

def fibonacci(n: int) -> int:
    print(f"fibonacci({n})")
    if n in [0, 1]:
        return n
    else:
        return fibonacci(n=n-1) + fibonacci(n=n-2)

@pytest.mark.parametrize("p",[0, 0.5, 1])
def test_swarming_fibonacci_small(tmpdir,p):
    # tmpdir = 20*"Q" + str(int(time.time()))
    global fibonacci
    address = None
    with _PortalTester(SwarmingPortal
            , tmpdir, n_background_workers=0) as t:
        fibonacci_new = pure()(fibonacci)
        address = fibonacci_new.swarm(n=8)

    with _PortalTester(SwarmingPortal
            , tmpdir, n_background_workers=7
            , p_consistency_checks=p) as t:
        address._invalidate_cache()
        address._portal = t.portal
        result = address.get()
        assert result == 21