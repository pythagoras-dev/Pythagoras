from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._080_pure_code_portals.pure_decorator import pure


# def test_run_grid(tmpdir):
#     with _PortalTester(PureCodePortal, tmpdir) as t:
#
#         @pure()
#         def my_sum(x: float, y:float) -> float:
#             return x + y
#
#         grid = dict(
#             x=[1, 2, 5]
#             ,y=[10, 100, 1000])
#
#         addrs = my_sum.run_grid(grid)
#         results = [a.get() for a in addrs]
#         assert sum(results) == 3354