from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure


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
    with _PortalTester(PureCodePortal, tmpdir):
        assert not isOdd(n=4,isEven=isEven, isOdd=isOdd)
        assert isEven(n=4,isEven=isEven, isOdd=isOdd)


# def test_one_decorator_odd(tmpdir):
#     with _PortalTester(PureCodePortal, tmpdir):
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
#     with _PortalTester(PureCodePortal, tmpdir):
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

def test_two_decorators(tmpdir):
    # tmpdir = "YIYIYIYIYIYIYIYIYIYIYIYIYIYIYIY"
    with _PortalTester(PureCodePortal
            , tmpdir.mkdir("asd")
            ):
        global isEven, isOdd
        old_isOdd = isOdd
        old_isEven = isEven

        isEven = pure()(isEven)
        isOdd = pure()(isOdd)
        for i in range(4):
            assert not isOdd(n=24, isEven=isEven, isOdd=isOdd)
            assert isEven(n=24, isEven=isEven, isOdd=isOdd)

        isEven, isOdd = (isEven.fix_kwargs(isEven=isEven, isOdd=isOdd)
                         , isOdd.fix_kwargs(isEven=isEven, isOdd=isOdd))

        for i in range(3):
            assert not isOdd(n=24)
            assert isEven(n=24)

        isEven = old_isEven
        isOdd = old_isOdd