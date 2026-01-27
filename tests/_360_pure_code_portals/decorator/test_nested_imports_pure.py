from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure


def test_nested_from_import(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        @pure()
        def f(x:float)->float:
            from math import sqrt
            return sqrt(x)

        assert f(x=4) == 2


def test_nested_import_as(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        @pure()
        def f(x:float)->float:
            import math as mm
            return mm.sin(x)

        assert f(x=0) == 0

def test_nested_from_import_as(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        @pure()
        def f(x:float)->float:
            from math import log as l
            return l(x)

        assert f(x=1) == 0