import pytest

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._040_logging_code_portals import (
    LoggingCodePortal, logging, LoggingFn)


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
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir):
        assert isOdd(n=4, isEven=isEven, isOdd=isOdd) == False
        assert isEven(n=4, isOdd=isOdd, isEven=isEven) == True


@pytest.mark.parametrize("pr",[0,0.5,1])
def test_odd_even_two_decorators_logging(tmpdir,pr):
    # tmpdir = "ODD_EVEN_TWO_DECORATORS_LOGGING_" + str(int(time.time()))
    with _PortalTester(LoggingCodePortal, root_dict=tmpdir
            ,p_consistency_checks=pr) as l:
        global isEven, isOdd
        N=7
        for i in range(N):
            oldIsEven = isEven
            oldIsOdd = isOdd

            isEven = logging(excessive_logging=True)(isEven)
            assert isinstance(isEven, LoggingFn)
            isOdd = logging(excessive_logging=True)(isOdd)
            assert isinstance(isOdd, LoggingFn)

            assert isOdd(n=i, isEven=isEven, isOdd=isOdd) == bool(i%2)
            assert isEven(n=i, isEven=isEven, isOdd=isOdd) == bool((i+1)%2)

            isEven = oldIsEven
            isOdd = oldIsOdd

        assert l.portal.get_number_of_linked_functions() == 0
        assert len([k for k in l.portal._value_store.keys() if k[2]== "bool"]) == 2
        assert len([k for k in l.portal._value_store.keys() if k[2]== "int"]) == N
        assert len([k for k in l.portal._value_store.keys() if k[2]== "packedkwargs_len_3"]) == N
