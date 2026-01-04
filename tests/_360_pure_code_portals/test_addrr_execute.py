from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure



def simple_func(n: int) -> int:
    return 10 + n


def complex_func(n: int) -> int:
    return simple_func(n=n)

def test_addrr_execute(tmpdir):
    # tmpdir = "TTTTTTTTTTTTTTTTTTTTT"

    with _PortalTester(PureCodePortal, tmpdir):
        global simple_func, complex_func
        simple_func = pure()(simple_func)
        addr_10_simple = simple_func.get_address(n=0)
        # complex_func = pure()(complex_func)
        # addr_10_complex = complex_func.get_address(n=0)


    with _PortalTester(PureCodePortal, tmpdir) as t:
        addr_10_simple._invalidate_cache()
        addr_10_simple._portal = t.portal
        assert addr_10_simple.execute() == 10
        assert addr_10_simple.fn(n=1) == 11

