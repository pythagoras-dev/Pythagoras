from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._410_swarming_portals.swarming_portals import (
    SwarmingPortal)
import pythagoras as pth


def factorial(n: int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n - 1)

def get_factorial_address(n:int, dir):
    with _PortalTester(SwarmingPortal
            , dir, max_n_workers=0):
        new_factorial = pth.pure()(factorial)
        address = new_factorial.swarm(n=n)
        address._invalidate_cache()
        return address

def test_swarming_factorial(tmpdir):
    # tmpdir = "FACTORIAL_SWARMING_TEST_"+ str(int(time.time()))
    address = get_factorial_address(n=5, dir=tmpdir)
    with _PortalTester(SwarmingPortal
            , tmpdir
            , max_n_workers=2
            ) as t:
        address._portal = t.portal
        assert address.get() == 120
