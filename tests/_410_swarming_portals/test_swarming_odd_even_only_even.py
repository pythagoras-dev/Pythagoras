from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._410_swarming_portals.swarming_portals import (
    SwarmingPortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure
import pytest


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


def test_one_decorator_odd(tmpdir):
    global isEven, isOdd
    _address = None
    with _PortalTester(SwarmingPortal
            , tmpdir, max_n_workers=0):
        with pytest.raises(Exception):
            isEven = pure()(isEven)
            isOdd.swarm(n=400)