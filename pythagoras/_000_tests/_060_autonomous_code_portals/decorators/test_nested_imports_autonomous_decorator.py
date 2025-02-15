from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._060_autonomous_code_portals import *


def test_nested_from_import(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:

        @autonomous()
        def f(x:float)->float:
            from math import sqrt
            return sqrt(x)

        assert f(x=4) == 2


def test_nested_import_as(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:

        @autonomous()
        def f(x:float)->float:
            import math as mm
            return mm.sin(x)

        assert f(x=0) == 0


def test_nested_from_import_as(tmpdir):
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:

        @autonomous()
        def f(x:float)->float:
            from math import log as l
            return l(x)

        assert f(x=1) == 0

