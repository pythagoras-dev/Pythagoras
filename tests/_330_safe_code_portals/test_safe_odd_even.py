
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._330_safe_code_portals import (
    SafeCodePortal, safe, SafeFn)


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


def test_odd_even_no_decorators_logging(tmpdir):
    with _PortalTester(SafeCodePortal, root_dict=tmpdir):
        assert not isOdd(n=4, isEven=isEven, isOdd=isOdd)
        assert isEven(n=4, isOdd=isOdd, isEven=isEven)



def test_odd_even_two_decorators_logging(tmpdir):
    # tmpdir = "ODD_EVEN_TWO_DECORATORS_LOGGING_" + str(int(time.time()))
    with _PortalTester(SafeCodePortal, root_dict=tmpdir) as t:
        global isEven, isOdd
        N=5
        for i in range(N):
            oldIsEven = isEven
            oldIsOdd = isOdd

            isEven = safe(excessive_logging=True)(isEven)
            assert isinstance(isEven, SafeFn)
            isOdd = safe(excessive_logging=True)(isOdd)
            assert isinstance(isOdd, SafeFn)

            assert isOdd(n=i, isEven=isEven, isOdd=isOdd) == bool(i%2)
            assert isEven(n=i, isEven=isEven, isOdd=isOdd) == bool((i+1)%2)

            isEven = oldIsEven
            isOdd = oldIsOdd

        assert len([k for k in t.portal.global_value_store.keys() if k[2]=="bool"]) == 2
        assert len([k for k in t.portal.global_value_store.keys() if k[2]=="int"]) == N
        assert len([k for k in t.portal.global_value_store.keys() if k[2]=="packedkwargs_len_3"]) == N
