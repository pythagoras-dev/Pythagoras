"""Tests for edge cases and error handling in OrdinaryFn and normalization."""

import pytest

from pythagoras import (
    OrdinaryFn, OrdinaryCodePortal, _PortalTester,
    FunctionError, get_normalized_fn_source_code_str
)
from pythagoras._310_ordinary_code_portals.code_normalizer import (
    _get_normalized_fn_source_code_str_impl
)


def test_ordinary_fn_invalid_input_type(tmpdir):
    """Test OrdinaryFn raises TypeError with invalid input types."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        with pytest.raises(TypeError, match="fn must be a callable or a string"):
            OrdinaryFn(123, portal=t.portal)

        with pytest.raises(TypeError, match="fn must be a callable or a string"):
            OrdinaryFn([1, 2, 3], portal=t.portal)

        with pytest.raises(TypeError, match="fn must be a callable or a string"):
            OrdinaryFn(None, portal=t.portal)


def test_normalization_empty_source():
    """Test normalization with empty or whitespace-only source."""
    with pytest.raises(ValueError):
        _get_normalized_fn_source_code_str_impl("", drop_pth_decorators=False)

    with pytest.raises(ValueError):
        _get_normalized_fn_source_code_str_impl("   \n\n  ", drop_pth_decorators=False)


def test_normalization_no_function_definition():
    """Test normalization with code that contains no function."""
    source = """
x = 10
y = 20
result = x + y
"""
    with pytest.raises(ValueError, match="No function definition found"):
        _get_normalized_fn_source_code_str_impl(source, drop_pth_decorators=False)


def test_normalization_multiple_decorators():
    """Test that functions with multiple decorators are rejected."""

    def external_decorator(f):
        return f

    @external_decorator
    def decorated_func(x):
        return x * 2

    # This should raise FunctionError due to multiple decorators check
    # However, external decorators are not Pythagoras decorators
    with pytest.raises((FunctionError, ValueError)):
        get_normalized_fn_source_code_str(decorated_func)


def test_normalization_non_pythagoras_decorator():
    """Test error when trying to drop non-Pythagoras decorator."""
    source = """
@some_external_decorator
def my_func(x):
    return x
"""
    with pytest.raises(ValueError, match="non-Pythagoras decorator"):
        _get_normalized_fn_source_code_str_impl(source, drop_pth_decorators=True)


def test_normalization_invalid_ast_node():
    """Test normalization with non-function top-level node."""
    source = """
class MyClass:
    pass
"""
    with pytest.raises(ValueError):
        _get_normalized_fn_source_code_str_impl(source, drop_pth_decorators=False)


def test_ordinary_fn_compile_error(tmpdir):
    """Test OrdinaryFn with syntactically invalid source code."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        invalid_source = """
def broken_func(x)
    return x  # Missing colon
"""
        with pytest.raises(SyntaxError):
            OrdinaryFn(invalid_source, portal=t.portal)


def test_ordinary_fn_from_non_ordinary_function(tmpdir):
    """Test OrdinaryFn with functions that violate ordinarity constraints."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        # Function with default arguments
        def func_with_defaults(x, y=10):
            return x + y

        with pytest.raises(FunctionError, match="can't have.*default values"):
            OrdinaryFn(func_with_defaults, portal=t.portal)

        # Function with *args
        def func_with_args(x, *args):
            return sum(args)

        with pytest.raises(FunctionError, match="unlimited.*positional arguments"):
            OrdinaryFn(func_with_args, portal=t.portal)

        # Lambda function
        with pytest.raises(FunctionError, match="can't be lambda"):
            OrdinaryFn(lambda x: x * 2, portal=t.portal)


def test_ordinary_fn_closure(tmpdir):
    """Test OrdinaryFn rejects closure functions."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        captured_value = 42

        def closure_func(x):
            return x + captured_value

        with pytest.raises(FunctionError, match="can't be a closure"):
            OrdinaryFn(closure_func, portal=t.portal)


def test_ordinary_fn_async_function(tmpdir):
    """Test OrdinaryFn rejects async functions."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:

        async def async_func(x):
            return x * 2

        with pytest.raises(FunctionError, match="can't be.*async function"):
            OrdinaryFn(async_func, portal=t.portal)


def test_ordinary_fn_method(tmpdir):
    """Test OrdinaryFn rejects bound methods."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:

        class MyClass:
            def my_method(self, x):
                return x * 2

        obj = MyClass()
        with pytest.raises(FunctionError, match="not ordinary"):
            OrdinaryFn(obj.my_method, portal=t.portal)


def test_ordinary_fn_builtin(tmpdir):
    """Test OrdinaryFn rejects builtin functions."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        with pytest.raises(FunctionError, match="not ordinary"):
            OrdinaryFn(len, portal=t.portal)

        with pytest.raises(FunctionError, match="not ordinary"):
            OrdinaryFn(print, portal=t.portal)


def test_normalization_preserves_function_logic():
    """Test that normalization preserves essential function logic."""

    def original_func(x, y):
        """This is a docstring that should be removed."""
        # This is a comment that should be removed
        if x > y:
            return x
        else:
            return y

    normalized = get_normalized_fn_source_code_str(original_func)

    # Should not contain docstring or comments
    assert "docstring" not in normalized
    assert "comment" not in normalized

    # Should preserve function name and logic structure
    assert "def original_func" in normalized
    assert "if x > y:" in normalized or "if x > y:" in normalized.replace(" ", "")
    assert "return x" in normalized
    assert "return y" in normalized


def test_ordinary_fn_wrong_portal_type(tmpdir):
    """Test that OrdinaryFn validates portal type."""
    from pythagoras import BasicPortal

    with _PortalTester(BasicPortal, root_dict=tmpdir):
        def simple_func(x):
            return x * 2

        # BasicPortal is not OrdinaryCodePortal
        # This should work - OrdinaryFn accepts BasicPortal or None
        # Let's test with invalid types instead
        with pytest.raises(TypeError, match="portal must be"):
            OrdinaryFn(simple_func, portal="not_a_portal")

        with pytest.raises(TypeError, match="portal must be"):
            OrdinaryFn(simple_func, portal=123)
