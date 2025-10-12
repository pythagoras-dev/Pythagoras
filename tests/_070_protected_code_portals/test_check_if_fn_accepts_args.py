import pytest

from pythagoras._070_protected_code_portals.fn_arg_names_checker import (
    check_if_fn_accepts_args)


def test_single_function_with_kwargs():
    """
    If the function has a **kwargs param, it can accept any named argument.
    """
    source_code = """
def example(a, b=1, **kwargs):
    pass
"""
    # With **kwargs, it should return True for any arbitrary argument name.
    assert check_if_fn_accepts_args(["x", "y"], source_code) is True
    assert check_if_fn_accepts_args(["anything"], source_code) is True

def test_single_function_no_kwargs_all_args_present():
    """
    If the function does NOT have **kwargs, we must check if all required_arg_names are in its signature.
    """
    source_code = """
def example(a, b, c=3):
    pass
"""
    # This function explicitly has 'a', 'b', 'c'.
    assert check_if_fn_accepts_args(["a"], source_code) is True
    assert check_if_fn_accepts_args(["a", "b"], source_code) is True
    assert check_if_fn_accepts_args(["a", "b", "c"], source_code) is True

def test_single_function_no_kwargs_some_args_missing():
    """
    When one or more required_arg_names are missing and there's no **kwargs, return False.
    """
    source_code = """
def example(a, b, c=3):
    pass
"""
    # This function only has 'a', 'b', 'c'.
    assert check_if_fn_accepts_args(["d"], source_code) is False
    assert check_if_fn_accepts_args(["a", "d"], source_code) is False

def test_function_with_keyword_only_args():
    """
    Test function with keyword-only arguments (after a '*').
    """
    source_code = """
def example(a, *, x, y=10):
    pass
"""
    # The function has 'a' (positional) and keyword-only 'x' and 'y'.
    # No **kwargs, so only these three are valid param names.
    assert check_if_fn_accepts_args(["a", "x", "y"], source_code) is True
    assert check_if_fn_accepts_args(["z"], source_code) is False
    assert check_if_fn_accepts_args(["x", "z"], source_code) is False

def test_function_with_star_args_but_no_kwargs():
    """
    *args doesn't affect named arguments, only positional.
    """
    source_code = """
def example(a, b, *args):
    pass
"""
    # Only 'a' and 'b' are valid named arguments. *args doesn't handle keyword arguments.
    assert check_if_fn_accepts_args(["a"], source_code) is True
    assert check_if_fn_accepts_args(["b"], source_code) is True
    assert check_if_fn_accepts_args(["c"], source_code) is False

def test_no_function_definition_raises_value_error():
    """
    If the provided source code doesn't contain any function definitions,
    we expect a ValueError to be raised.
    """
    source_code = """
# Just a comment, no function here
x = 10
"""
    with pytest.raises(ValueError):
        check_if_fn_accepts_args(["a"], source_code)


def test_empty_arg_names_list():
    """
    If required_arg_names is empty, it should always return True (no requirements to fulfill).
    """
    source_code = """
def example(a, b, c=3):
    pass
"""
    assert check_if_fn_accepts_args([], source_code) is True

def test_function_with_kwargs_in_different_param_position():
    """
    Confirm behavior if **kwargs is not the last parameter (an unusual, but possible scenario).
    """
    source_code = """
def example(a, **kwargs):
    pass
"""
    assert check_if_fn_accepts_args(["anything"], source_code) is True
    assert check_if_fn_accepts_args(["a", "extra"], source_code) is True
