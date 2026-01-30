import pytest

from pythagoras import FunctionError
from pythagoras._310_ordinary_code_portals.function_processing import assert_ordinarity



def test_lambdas():
    with pytest.raises(FunctionError):
        assert_ordinarity(lambda x: x**2)


class DemoClass:
    def regular_method(self):
        pass

    @classmethod
    def class_method(cls):
        pass

    @staticmethod
    def static_method():
        pass

def test_methods():
    demo_obj = DemoClass()
    with pytest.raises(FunctionError):
        assert_ordinarity(demo_obj.regular_method)
    with pytest.raises(FunctionError):
        assert_ordinarity(demo_obj.class_method)

    # TODO: decide how to handle static methods
    # currently they are treated as ordinary functions
    # with pytest.raises(AssertionError):
    #     assert_ordinarity(demo_obj.static_method)

def outer_function():
    return 0

def test_ordinary_functions():
    def inner_function():
        return 1

    assert_ordinarity(outer_function)
    assert_ordinarity(inner_function)

def test_closure():
    i = 5
    def inner_function():
        return i

    with pytest.raises(FunctionError):
        assert_ordinarity(inner_function)

def test_builtin_functions():
    with pytest.raises(FunctionError):
        assert_ordinarity(print)
    with pytest.raises(FunctionError):
        assert_ordinarity(len)

def test_async_functions():
    async def async_function():
        pass

    with pytest.raises(FunctionError):
        assert_ordinarity(async_function)

def test_default_args():
    def func_with_defaults(a=1):
        pass

    with pytest.raises(FunctionError):
        assert_ordinarity(func_with_defaults)

def test_var_args():
    def func_with_var_args(*args):
        pass

    with pytest.raises(FunctionError):
        assert_ordinarity(func_with_var_args)

def test_var_kwargs_allowed():
    """**kwargs are allowed in ordinary functions."""
    def func_with_kwargs(**kwargs):
        pass

    assert_ordinarity(func_with_kwargs)


def test_positional_only_params():
    """Positional-only parameters are not allowed in ordinary functions."""
    def func_requiring_positional_arg(a, /, b):
        pass

    with pytest.raises(FunctionError):
        assert_ordinarity(func_requiring_positional_arg)
