import pytest
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._080_pure_code_portals.pure_decorator import pure


def isEven(n, isEven, isOdd):
    if n == 0:
        return True
    else:
        return isOdd(n = n-1,isEven=isEven, isOdd=isOdd)


def isOdd(n, isEven, isOdd):
    if n == 0:
        return False
    else:
        return isEven(n = n-1,isEven=isEven, isOdd=isOdd)


def test_no_decorators(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:
        assert isOdd(n=4,isEven=isEven, isOdd=isOdd) == False
        assert isEven(n=4,isEven=isEven, isOdd=isOdd) == True


# def test_one_decorator_odd(tmpdir):
#     with _PortalTester(PureCodePortal, tmpdir) as t:
#         global isEven,  isOdd
#         old_isOdd = isOdd
#         old_isEven = isEven
#
#         isEven = pure()(isEven)
#         with pytest.raises(Exception):
#             assert isOdd(n=4) == False
#
#         isEven = old_isEven
#         isOdd = old_isOdd
#
#
# def test_one_decorator_even(tmpdir):
#     with _PortalTester(PureCodePortal, tmpdir) as t:
#         global isEven,  isOdd
#         old_isOdd = isOdd
#         old_isEven = isEven
#
#         isEven = pure()(isEven)
#         with pytest.raises(Exception):
#             assert isEven(n=4) == True
#
#         isEven = old_isEven
#         isOdd = old_isOdd

@pytest.mark.parametrize("p",[0, 0.5, 1])
def test_two_decorators(tmpdir,p):
    # tmpdir = "YIYIYIYIYIYIYIYIYIYIYIYIYIYIYIY"
    with _PortalTester(PureCodePortal
            , tmpdir.mkdir("asd")
            , p_consistency_checks = p) as t:
        global isEven, isOdd
        old_isOdd = isOdd
        old_isEven = isEven

        isEven = pure()(isEven)
        isOdd = pure()(isOdd)
        for i in range(4):
            assert isOdd(n=24, isEven=isEven, isOdd=isOdd) == False
            assert isEven(n=24, isEven=isEven, isOdd=isOdd) == True

        isEven, isOdd = (isEven.fix_kwargs(isEven=isEven, isOdd=isOdd)
                         , isOdd.fix_kwargs(isEven=isEven, isOdd=isOdd))

        for i in range(3):
            assert isOdd(n=24) == False
            assert isEven(n=24) == True

        isEven = old_isEven
        isOdd = old_isOdd

        value_store = t.portal._value_store
        assert value_store.consistency_checks_failed == 0
        if p > 0:
            assert value_store.consistency_checks_attempted > 0
        else:
            assert value_store.consistency_checks_attempted == 0

        execution_results = t.portal._execution_results
        assert execution_results.consistency_checks_failed == 0
        if p > 0:
            assert execution_results.consistency_checks_attempted > 0
        else:
            assert execution_results.consistency_checks_attempted == 0