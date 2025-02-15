from pythagoras._020_ordinary_code_portals.function_processing import (
    count_parameters_with_defaults)


def test_no_defaults():
    """Test a function with no default parameters."""
    def no_defaults(a, b, c):
        pass

    assert count_parameters_with_defaults(no_defaults) == 0


def test_some_defaults():
    """Test a function with some default parameters."""
    def some_defaults(a, b=1, c="hello", d=None):
        pass

    assert count_parameters_with_defaults(some_defaults) == 3


def test_all_defaults():
    """Test a function where all parameters have default values."""
    def all_defaults(a=10, b=20, c="default"):
        pass

    assert count_parameters_with_defaults(all_defaults) == 3


def test_var_args_no_defaults():
    """Test a function with *args and **kwargs, no defaults."""
    def var_args_no_defaults(a, *args, **kwargs):
        pass

    # *args and **kwargs themselves are not considered default parameters
    # unless they are assigned a default in some unusual way (which is rare).
    assert count_parameters_with_defaults(var_args_no_defaults) == 0


def test_combined_defaults_and_var_args():
    """Test a function with both defaults and var-args."""
    def combined_defaults(a, b=1, *args, c="hello", **kwargs):
        pass

    # Here, 'b' and 'c' have defaults.
    assert count_parameters_with_defaults(combined_defaults) == 2