from copy import deepcopy
from pythagoras import BasicPortal
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._090_swarming_portals.swarming_portals import (
    SwarmingPortal, _process_random_execution_request)
from pythagoras._070_pure_functions.pure_decorator import pure
import pythagoras as pth


def isEven(n):
    if n == 0:
        return True
    else:
        return isOdd(n = n-1)


def isOdd(n):
    if n == 0:
        return False
    else:
        return isEven(n = n-1)


def test_no_decorators(tmpdir):
    with _PortalTester(SwarmingPortal
            , tmpdir, n_background_workers=0) as t:
        assert isOdd(n=400) == False
        assert isEven(n=400) == True

def test_two_decorators(tmpdir):
    global isEven, isOdd
    addr = None
    with _PortalTester(SwarmingPortal
            , tmpdir, n_background_workers=0) as t:
        isEven_pure = pure()(isEven)
        isOdd_pure = pure()(isOdd)
        addr = isEven_pure.swarm(n=40)

    with _PortalTester(SwarmingPortal
            , tmpdir, n_background_workers=8) as t:
        addr._invalidate_cache()
        addr._portal = t.portal
        assert addr.get() == True
