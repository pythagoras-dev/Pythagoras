from pythagoras import PureFn
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._080_pure_code_portals.pure_decorator import pure
import pytest



def f_nstd():
    return 5

def g_nstd(f_nstd):
    return f_nstd()

def test_2_nested_calls(tmpdir):
    global f_nstd, g_nstd
    with _PortalTester(PureCodePortal, tmpdir) as t:
        assert g_nstd(f_nstd=f_nstd) == 5
        g_nstd = pure()(g_nstd)
        f_nstd = pure()(f_nstd)
        assert isinstance(f_nstd, PureFn)
        assert isinstance(g_nstd, PureFn)
        assert g_nstd(f_nstd=f_nstd) == 5