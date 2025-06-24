from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._090_swarming_portals.swarming_portals import (
    SwarmingPortal)
from src.pythagoras._080_pure_code_portals.pure_decorator import pure

def fibonacci(n: int) -> int:
    print(f"fibonacci({n})")
    if n in [0, 1]:
        return n
    else:
        return fibonacci(n=n-1) + fibonacci(n=n-2)

def test_swarming_fibonacci(tmpdir):
    # tmpdir = 20*"Q" + str(int(time.time()))
    global fibonacci
    address = None
    with _PortalTester(SwarmingPortal
            , tmpdir, max_n_workers=0) as t:
        fibonacci = pure()(fibonacci)
        address = fibonacci.swarm(n=50)
        address._invalidate_cache()

    with _PortalTester(SwarmingPortal
            , tmpdir, max_n_workers=5) as t:
        address._invalidate_cache()
        assert address.get() == 12586269025