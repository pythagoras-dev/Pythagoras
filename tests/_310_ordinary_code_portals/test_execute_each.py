import pytest

from pythagoras import OrdinaryFn, _PortalTester, OrdinaryCodePortal


def simple_add(a, b):
    return a + b


def double(x):
    return x * 2


def my_sum(x, y):
    return x + y


def test_execute_each(tmpdir):
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        f = OrdinaryFn(simple_add)

        results = f.execute_each([
            dict(a=1, b=2),
            dict(a=3, b=4),
            dict(a=10, b=20),
        ])
        assert results == [3, 7, 30]


def test_execute_each_empty(tmpdir):
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        f = OrdinaryFn(double)

        results = f.execute_each([])
        assert results == []


def test_execute_each_type_errors(tmpdir):
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        f = OrdinaryFn(double)

        with pytest.raises(TypeError, match="list or tuple"):
            f.execute_each("not a list")

        with pytest.raises(TypeError, match="must be a dict"):
            f.execute_each([dict(x=1), "not a dict"])


def test_execute_grid(tmpdir):
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        f = OrdinaryFn(my_sum)

        grid = dict(x=[1, 2, 5], y=[10, 100, 1000])
        results = f.execute_grid(grid)
        assert sum(results) == 3354


def test_execute_grid_single_param(tmpdir):
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        f = OrdinaryFn(double)

        results = f.execute_grid(dict(x=[1, 2, 3]))
        assert results == [2, 4, 6]
