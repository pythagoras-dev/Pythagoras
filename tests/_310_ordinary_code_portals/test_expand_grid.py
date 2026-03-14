from pythagoras._310_ordinary_code_portals.ordinary_portal_core_classes import (
    _expand_grid)


def test_expand_grid_two_params():
    result = _expand_grid(dict(x=[1, 2], y=[10, 20]))
    assert result == [
        dict(x=1, y=10),
        dict(x=1, y=20),
        dict(x=2, y=10),
        dict(x=2, y=20),
    ]


def test_expand_grid_single_param():
    result = _expand_grid(dict(x=[1, 2, 3]))
    assert result == [dict(x=1), dict(x=2), dict(x=3)]


def test_expand_grid_three_params():
    result = _expand_grid(dict(a=[1, 2], b=["x"], c=[True, False]))
    assert len(result) == 4
    assert dict(a=1, b="x", c=True) in result
    assert dict(a=2, b="x", c=False) in result


def test_expand_grid_empty_values():
    result = _expand_grid(dict(x=[], y=[1, 2]))
    assert result == []


def test_expand_grid_empty_dict():
    result = _expand_grid({})
    assert result == [{}]
