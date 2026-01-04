from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def func_with_posonly_and_kwonly(a, b, /, c, d, *, e, f):
    """Function with positional-only and keyword-only arguments."""
    return a + b + c + d + e + f


def test_posonlyargs_and_kwonlyargs():
    """Test that posonlyargs and kwonlyargs are recognized as local variables."""
    result = _analyze_names_in_function(func_with_posonly_and_kwonly)
    analyzer = result['analyzer']

    # All parameters should be local
    assert analyzer.names.local == {'a', 'b', 'c', 'd', 'e', 'f'}
    # No parameters should appear as unclassified
    assert analyzer.names.unclassified_deep == set()
    # All parameters should be accessible
    assert analyzer.names.accessible == {'a', 'b', 'c', 'd', 'e', 'f'}
    # No globals or nonlocals
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    # No imports
    assert analyzer.names.imported == set()


def func_with_mixed_arg_types(pos1, pos2, /, std1, std2, kw1, kw2):
    """Function with positional-only, standard, and keyword-only arguments."""
    return pos1 + pos2 + std1 + std2 + kw1 + kw2


def test_mixed_argument_types():
    """Test that mixed argument types are recognized as local variables."""
    result = _analyze_names_in_function(func_with_mixed_arg_types)
    analyzer = result['analyzer']

    # All parameters should be local
    expected_locals = {'pos1', 'pos2', 'std1', 'std2', 'kw1', 'kw2'}
    assert analyzer.names.local == expected_locals
    # No unclassified names
    assert analyzer.names.unclassified_deep == set()
    # No globals or nonlocals
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()


def func_posonly_only(a, b, /):
    """Function with only positional-only arguments."""
    return a + b


def test_posonly_only():
    """Test that positional-only arguments work correctly."""
    result = _analyze_names_in_function(func_posonly_only)
    analyzer = result['analyzer']

    assert analyzer.names.local == {'a', 'b'}
    assert analyzer.names.unclassified_deep == set()


def func_kwonly_only(*, a, b):
    """Function with only keyword-only arguments."""
    return a + b


def test_kwonly_only():
    """Test that keyword-only arguments work correctly."""
    result = _analyze_names_in_function(func_kwonly_only)
    analyzer = result['analyzer']

    assert analyzer.names.local == {'a', 'b'}
    assert analyzer.names.unclassified_deep == set()
