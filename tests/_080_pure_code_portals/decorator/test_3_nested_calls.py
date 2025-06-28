from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._080_pure_code_portals.pure_decorator import pure


def a():
    return 2

def b(a):
    return a()*2

def c(b,a):
    return b(a=a)*2

def test_2_nested_calls(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        global a, b, c

        assert a() == 2
        assert b(a) == 4
        assert c(b,a) == 8


        c = pure()(c)
        a = pure()(a)
        b = pure()(b)

        assert c(b=b,a=a) == 8