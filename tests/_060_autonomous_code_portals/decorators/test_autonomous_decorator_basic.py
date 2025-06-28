from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._060_autonomous_code_portals import *

def test_strictly_autonomous(tmpdir):

    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):

        def f(a: int):
            b = 24
            return a + b

        f = autonomous()(f)

        assert isinstance(f, AutonomousFn)
        assert f(a=10) == 34


def h(a:int):
    b=100
    return a+b


def test_autonomous(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):

        @autonomous()
        def zyx(a: int):
            b = 10
            return a + b

        assert isinstance(zyx, AutonomousFn)
        assert zyx(a=10) == 20
