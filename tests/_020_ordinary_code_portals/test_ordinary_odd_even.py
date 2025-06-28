from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._020_ordinary_code_portals import (
    OrdinaryCodePortal, ordinary, OrdinaryFn)


def isEven(n, isOdd, isEven):
    if n == 0:
        return True
    else:
        return isOdd(n = n-1, isEven=isEven, isOdd=isOdd)


def isOdd(n, isEven, isOdd):
    if n == 0:
        return False
    else:
        return isEven(n = n-1, isOdd=isOdd, isEven=isEven)


def test_odd_even_no_decorators_ordinary(tmpdir):
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        assert isOdd(n=4, isEven=isEven, isOdd=isOdd) == False
        assert isEven(n=4, isOdd=isOdd, isEven=isEven) == True


def test_odd_even_two_decorators_ordinary(tmpdir):
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        global isEven, isOdd
        oldIsEven = isEven
        oldIsOdd = isOdd

        isEven = ordinary()(isEven)
        assert isinstance(isEven, OrdinaryFn)
        isOdd = ordinary()(isOdd)
        assert isinstance(isOdd, OrdinaryFn)

        assert isOdd(n=4, isEven=isEven, isOdd=isOdd) == False
        assert isEven(n=4, isEven=isEven, isOdd=isOdd) == True

        isEven = oldIsEven
        isOdd = oldIsOdd