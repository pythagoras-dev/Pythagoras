"""Test del statement tracking in names_usage_analyzer.

This module tests that the analyzer correctly handles del statements,
which establish local scope in Python just like assignments.
"""

from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def test_del_after_assignment():
    """Test del on a variable that was previously assigned."""
    code = """
def func():
    x = 10
    del x
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # x should be in locals (from assignment)
    assert 'x' in analyzer.names.local
    assert 'x' in analyzer.names.accessible


def test_del_without_assignment():
    """Test del on a variable without prior assignment.

    In Python, 'del x' establishes x as a local variable even without
    prior assignment. This is compile-time behavior - at runtime it
    will raise UnboundLocalError, but the compiler treats x as local.
    """
    code = """
def func():
    del x
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # x should be tracked as local (del establishes local scope)
    assert 'x' in analyzer.names.local, f"Expected 'x' in locals, got: {analyzer.names.local}"
    assert 'x' in analyzer.names.accessible


def test_del_multiple_targets():
    """Test del with multiple targets."""
    code = """
def func():
    x = 1
    y = 2
    del x, y
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # Both x and y should be in locals
    assert 'x' in analyzer.names.local
    assert 'y' in analyzer.names.local


def test_del_mixed_with_unassigned():
    """Test del with some assigned and some unassigned variables."""
    code = """
def func():
    x = 10
    del x, y, z
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # All should be tracked as local
    assert 'x' in analyzer.names.local
    assert 'y' in analyzer.names.local, f"Expected 'y' in locals (del establishes scope), got: {analyzer.names.local}"
    assert 'z' in analyzer.names.local, f"Expected 'z' in locals (del establishes scope), got: {analyzer.names.local}"


def test_del_vs_load():
    """Test that del is different from loading a variable."""
    code = """
def func():
    del x
    print(y)
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # x should be local (from del)
    assert 'x' in analyzer.names.local
    assert 'x' not in analyzer.names.unclassified_deep

    # y should be unclassified (just loaded, not assigned or deleted)
    assert 'y' in analyzer.names.unclassified_deep
    assert 'y' not in analyzer.names.local


def test_del_with_global():
    """Test del with global keyword."""
    code = """
def func():
    global x
    del x
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # x should be in explicitly_global_unbound_deep (from global keyword)
    assert 'x' in analyzer.names.explicitly_global_unbound_deep
    # del doesn't change that it's declared global
    assert 'x' in analyzer.names.accessible


def test_del_with_nonlocal():
    """Test del with nonlocal keyword."""
    code = """
def func():
    def inner():
        nonlocal x
        del x
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # x should be in explicitly_nonlocal_unbound_deep from the nested function
    assert 'x' in analyzer.names.explicitly_nonlocal_unbound_deep


def test_del_tuple_unpacking():
    """Test del with tuple unpacking-like syntax."""
    code = """
def func():
    x, y = 1, 2
    del (x, y)
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # Both should be in locals
    assert 'x' in analyzer.names.local
    assert 'y' in analyzer.names.local


def test_del_does_not_affect_attributes():
    """Test that del on attributes doesn't track the attribute name as local."""
    code = """
def func():
    obj = {}
    del obj['key']
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # obj should be local
    assert 'obj' in analyzer.names.local
    # 'key' should NOT be in locals (it's a dict key, not a variable)
    assert 'key' not in analyzer.names.local


def test_del_list_item():
    """Test del on list items."""
    code = """
def func():
    items = [1, 2, 3]
    del items[0]
    return items
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # items should be local
    assert 'items' in analyzer.names.local
    # No numbers should be in locals
    assert 0 not in analyzer.names.local


def test_del_in_nested_function():
    """Test del in nested function."""
    code = """
def func():
    x = 10
    def inner():
        del y
        return 42
    return inner()
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # x should be in outer function's locals
    assert 'x' in analyzer.names.local
    # y from nested function should not appear in outer (it's local to inner)
    # But inner is defined, so 'inner' should be local to outer
    assert 'inner' in analyzer.names.local
