from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from src.pythagoras._080_pure_code_portals.pure_decorator import pure



def f_before(**kwargs):
    return sum(kwargs.values())

def test_basics_pure_decorator_many_args(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        f_after = pure()(f_before)

        args_dict = dict()
        for i in range(10):
            arg_name = f"arg_{i}"
            args_dict[arg_name] = i
            assert f_after(**args_dict) == f_before(**args_dict)
