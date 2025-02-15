from copy import deepcopy
from pythagoras import BasicPortal
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._090_swarming_portals.swarming_portals import (
    SwarmingPortal, _process_random_execution_request)
from pythagoras._080_pure_code_portals.pure_decorator import pure
import pythagoras as pth
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
    address = None
    with _PortalTester(SwarmingPortal
            , tmpdir, n_background_workers=0) as t:
        with pytest.raises(Exception):
            isOdd = pure()(isOdd)
            address = isOdd.swarm(n=400)