from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure


def test_run_grid(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        @pure()
        def my_sum(x: float, y: float) -> float:
            return x + y

        grid = dict(
            x=[1, 2, 5]
            , y=[10, 100, 1000])

        addrs = my_sum.run_grid(grid)
        results = [a.get() for a in addrs]
        assert sum(results) == 3354


def test_swarm_grid(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        @pure()
        def my_sum(x: float, y: float) -> float:
            return x + y

        grid = dict(
            x=[1, 2, 5]
            , y=[10, 100, 1000])

        addrs = my_sum.swarm_grid(grid)
        assert len(addrs) == 9
        for addr in addrs:
            assert addr.execution_requested


def test_execute_grid(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        @pure()
        def my_sum(x: float, y: float) -> float:
            return x + y

        grid = dict(
            x=[1, 2, 5]
            , y=[10, 100, 1000])

        results = my_sum.execute_grid(grid)
        assert sum(results) == 3354
