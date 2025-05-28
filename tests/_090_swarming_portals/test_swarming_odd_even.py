from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._090_swarming_portals.swarming_portals import (
    SwarmingPortal)
from src.pythagoras._080_pure_code_portals.pure_decorator import pure


def isEven(n,isOdd, isEven):
    if n == 0:
        return True
    else:
        return isOdd(n = n-1, isOdd= isOdd, isEven= isEven)


def isOdd(n,isOdd, isEven):
    if n == 0:
        return False
    else:
        return isEven(n = n-1, isOdd= isOdd, isEven= isEven)


def test_no_decorators(tmpdir):
    with _PortalTester(SwarmingPortal
            , tmpdir, n_background_workers=0) as t:
        assert isOdd(n=400,isOdd= isOdd, isEven= isEven) == False
        assert isEven(n=400,isOdd= isOdd, isEven= isEven) == True

def test_two_decorators(tmpdir):
    global isEven, isOdd
    addr = None
    with _PortalTester(SwarmingPortal
            , tmpdir, n_background_workers=0) as t:
        isEven_pure = pure()(isEven)
        isOdd_pure = pure()(isOdd)
        addr = isEven_pure.swarm(n=10,isOdd= isOdd_pure, isEven= isEven_pure)

    with _PortalTester(SwarmingPortal
            , tmpdir, n_background_workers=8) as t:
        addr._invalidate_cache()
        addr._portal = t.portal
        assert addr.get() == True
