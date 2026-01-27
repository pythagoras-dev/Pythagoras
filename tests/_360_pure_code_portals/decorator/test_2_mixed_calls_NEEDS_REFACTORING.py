from pythagoras._340_autonomous_code_portals.autonomous_decorators import (
    autonomous)
from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure


def f_a():
    return 5

def f_i(f_a):
    return f_a()

def test_2_mixed_calls(tmpdir):
    global f_a, f_i
    with _PortalTester(PureCodePortal, tmpdir):
        assert f_a() == 5
        assert f_i(f_a) == 5
        f_a = autonomous()(f_a)
        f_i = pure()(f_i)

        assert f_a() == 5
        assert f_i(f_a=f_a) == 5 #TODO: Is it OK to accept autonomous here?

