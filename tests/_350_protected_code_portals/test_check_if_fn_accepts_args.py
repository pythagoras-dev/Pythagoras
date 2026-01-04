import pytest

from pythagoras._350_protected_code_portals.fn_arg_names_checker import (
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


def test_multiple_function_definitions_raises_value_error():
    """
    If the provided source code contains multiple function definitions,
    we expect a ValueError to be raised.
    """
    source_code = """
def func1(a, b):
    pass

def func2(x, y):
    pass
"""
    with pytest.raises(ValueError, match="Multiple function definitions"):
        check_if_fn_accepts_args(["a"], source_code)


def test_positional_only_parameters():
    """
    Test function with positional-only parameters (before '/').
    Positional-only parameters cannot be passed as keyword arguments.
    """
    source_code = """
def example(a, b, /, c, d=5):
    pass
"""
    # 'a' and 'b' are positional-only, so they shouldn't be in param_names
    # Only 'c' and 'd' can be passed as keyword arguments
    assert check_if_fn_accepts_args(["c"], source_code) is True
    assert check_if_fn_accepts_args(["d"], source_code) is True
    assert check_if_fn_accepts_args(["c", "d"], source_code) is True
    # 'a' and 'b' are positional-only, so they can't be accepted as keyword args
    assert check_if_fn_accepts_args(["a"], source_code) is False
    assert check_if_fn_accepts_args(["b"], source_code) is False
    assert check_if_fn_accepts_args(["a", "c"], source_code) is False


def test_positional_only_with_kwargs():
    """
    Test function with both positional-only parameters and **kwargs.
    With **kwargs present, any keyword argument name should be accepted.
    """
    source_code = """
def example(a, b, /, c, **kwargs):
    pass
"""
    # With **kwargs, all keyword argument names should be accepted
    assert check_if_fn_accepts_args(["a"], source_code) is True
    assert check_if_fn_accepts_args(["b"], source_code) is True
    assert check_if_fn_accepts_args(["c"], source_code) is True
    assert check_if_fn_accepts_args(["anything"], source_code) is True


def test_annotated_parameters():
    """
    Test that type annotations don't affect the logic.
    """
    source_code = """
def example(a: int, b: str, c: float = 3.14):
    pass
"""
    assert check_if_fn_accepts_args(["a"], source_code) is True
    assert check_if_fn_accepts_args(["a", "b", "c"], source_code) is True
    assert check_if_fn_accepts_args(["d"], source_code) is False


def test_defaulted_parameters():
    """
    Test that default values don't affect the logic.
    """
    source_code = """
def example(a=1, b=2, c=3):
    pass
"""
    assert check_if_fn_accepts_args(["a"], source_code) is True
    assert check_if_fn_accepts_args(["a", "b", "c"], source_code) is True
    assert check_if_fn_accepts_args(["d"], source_code) is False


def test_syntax_error_propagates():
    """
    Test that syntax errors in the supplied source are propagated.
    """
    source_code = """
def example(a, b
    pass
"""
    with pytest.raises(SyntaxError):
        check_if_fn_accepts_args(["a"], source_code)


def test_complex_signature_with_all_parameter_types():
    """
    Test a complex function signature with all parameter types combined.
    """
    source_code = """
def example(pos_only1, pos_only2, /, pos_or_kw1, pos_or_kw2=2, *args, kw_only1, kw_only2=10, **kwargs):
    pass
"""
    # With **kwargs, any keyword argument name should be accepted
    assert check_if_fn_accepts_args(["pos_only1"], source_code) is True
    assert check_if_fn_accepts_args(["pos_or_kw1"], source_code) is True
    assert check_if_fn_accepts_args(["kw_only1"], source_code) is True
    assert check_if_fn_accepts_args(["anything"], source_code) is True


def test_complex_signature_without_kwargs():
    """
    Test a complex function signature without **kwargs.
    """
    source_code = """
def example(pos_only1, pos_only2, /, pos_or_kw1, pos_or_kw2=2, *args, kw_only1, kw_only2=10):
    pass
"""
    # Only pos_or_kw1, pos_or_kw2, kw_only1, kw_only2 can be passed as keyword args
    assert check_if_fn_accepts_args(["pos_or_kw1"], source_code) is True
    assert check_if_fn_accepts_args(["pos_or_kw2"], source_code) is True
    assert check_if_fn_accepts_args(["kw_only1"], source_code) is True
    assert check_if_fn_accepts_args(["kw_only2"], source_code) is True
    assert check_if_fn_accepts_args(["pos_or_kw1", "kw_only1"], source_code) is True
    # pos_only1 and pos_only2 cannot be passed as keyword args
    assert check_if_fn_accepts_args(["pos_only1"], source_code) is False
    assert check_if_fn_accepts_args(["pos_only2"], source_code) is False
    # Random name not in signature
    assert check_if_fn_accepts_args(["random"], source_code) is False
