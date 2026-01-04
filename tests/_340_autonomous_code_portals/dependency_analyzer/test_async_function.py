from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def func_with_nested_async(x):
    """Function with nested async function."""
    async def inner(y):
        return x + y
    return inner


def test_async_function_parameters():
    """Test that async function parameters don't leak into parent scope."""
    result = _analyze_names_in_function(func_with_nested_async)
    analyzer = result['analyzer']

    # x and inner should be local
    assert 'x' in analyzer.names.local
    assert 'inner' in analyzer.names.local
    # y should NOT be in unclassified (it's local to async function)
    assert 'y' not in analyzer.names.unclassified_deep
    # No unclassified names expected
    assert analyzer.names.unclassified_deep == set()


def func_with_async_all_args(x):
    """Function with async function that has all argument types."""
    async def inner(a, b, /, c, d, *args, e, f, **kwargs):
        return a + b + c + d + sum(args) + e + f + sum(kwargs.values()) + x
    return inner


def test_async_with_all_arg_types():
    """Test async function with all argument types."""
    result = _analyze_names_in_function(func_with_async_all_args)
    analyzer = result['analyzer']

    # x and inner should be local
    assert analyzer.names.local == {'x', 'inner'}
    # Async function parameters should NOT leak
    for param in ['a', 'b', 'c', 'd', 'args', 'e', 'f', 'kwargs']:
        assert param not in analyzer.names.unclassified_deep
    # Only 'sum' should be unclassified
    assert analyzer.names.unclassified_deep == {'sum'}


def func_with_multiple_async(x):
    """Function with multiple nested async functions."""
    async def first(y):
        return x + y

    async def second(z):
        return x + z

    return first, second


def test_multiple_async_functions():
    """Test multiple nested async functions."""
    result = _analyze_names_in_function(func_with_multiple_async)
    analyzer = result['analyzer']

    # x, first, second should be local
    assert analyzer.names.local == {'x', 'first', 'second'}
    # y and z should NOT leak
    assert 'y' not in analyzer.names.unclassified_deep
    assert 'z' not in analyzer.names.unclassified_deep
    assert analyzer.names.unclassified_deep == set()


def func_async_with_import(x):
    """Function with async function that imports."""
    async def inner(y):
        import math
        return math.sqrt(y) + x
    return inner


def test_async_with_import():
    """Test async function with imports."""
    result = _analyze_names_in_function(func_async_with_import)
    analyzer = result['analyzer']

    # x and inner should be local
    assert analyzer.names.local == {'x', 'inner'}
    # math should be in imported_packages_deep
    assert 'math' in analyzer.imported_packages_deep
    # No unclassified names
    assert analyzer.names.unclassified_deep == set()


def func_async_uses_nonlocal(x):
    """Function with async function that uses nonlocal."""
    y = 10

    async def inner(z):
        nonlocal y
        y = y + z + x
        return y

    return inner, y


def test_async_with_nonlocal():
    """Test async function with nonlocal declaration."""
    result = _analyze_names_in_function(func_async_uses_nonlocal)
    analyzer = result['analyzer']

    # x, y, inner should be local
    assert 'x' in analyzer.names.local
    assert 'y' in analyzer.names.local
    assert 'inner' in analyzer.names.local
    # z should NOT leak
    assert 'z' not in analyzer.names.unclassified_deep
    # No unclassified names
    assert analyzer.names.unclassified_deep == set()


def func_nested_async_in_regular(x):
    """Function with regular function containing async function."""
    def regular(y):
        async def async_inner(z):
            return x + y + z
        return async_inner
    return regular


def test_nested_async_in_regular():
    """Test async function nested inside regular function."""
    result = _analyze_names_in_function(func_nested_async_in_regular)
    analyzer = result['analyzer']

    # x and regular should be local
    assert analyzer.names.local == {'x', 'regular'}
    # y and z should NOT leak (y is in regular, z is in async_inner)
    assert 'y' not in analyzer.names.unclassified_deep
    assert 'z' not in analyzer.names.unclassified_deep
    assert analyzer.names.unclassified_deep == set()


def func_with_deeply_nested_async(x):
    """Function with deeply nested async function."""
    def regular_nested(y):
        async def async_nested(z):
            return x + y + z
        return async_nested
    return regular_nested


def test_deeply_nested_async():
    """Test async function nested inside regular nested function."""
    result = _analyze_names_in_function(func_with_deeply_nested_async)
    analyzer = result['analyzer']

    # x and regular_nested should be local
    assert analyzer.names.local == {'x', 'regular_nested'}
    # y and z should NOT leak
    assert 'y' not in analyzer.names.unclassified_deep
    assert 'z' not in analyzer.names.unclassified_deep
    assert analyzer.names.unclassified_deep == set()
