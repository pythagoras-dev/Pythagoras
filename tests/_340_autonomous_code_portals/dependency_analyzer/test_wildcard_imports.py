"""Tests for wildcard import detection in autonomous functions.

Wildcard imports (from module import *) should be tracked by the analyzer.
They import names into the function's namespace, making them accessible.

Note: We test using string source code since Python doesn't allow
'from module import *' inside function definitions at the syntax level.
"""
from pythagoras._340_autonomous_code_portals.names_usage_analyzer import (
    _analyze_names_in_function
)


def test_wildcard_import_from_math():
    """Test that 'from math import *' is recognized as an import."""
    source = """
def func():
    from math import *
    return sqrt(16)
"""
    result = _analyze_names_in_function(source)
    analyzer = result['analyzer']

    # The wildcard '*' should appear in imported names
    assert '*' in analyzer.names.imported
    # 'math' package should be tracked
    assert 'math' in analyzer.imported_packages_deep
    # 'sqrt' is imported via wildcard, so it's accessible
    assert 'sqrt' in analyzer.names.accessible


def test_wildcard_import_makes_names_accessible():
    """Test that names used after wildcard import are accessible."""
    source = """
def func():
    from math import *
    return sqrt(25) + sin(0)
"""
    result = _analyze_names_in_function(source)
    analyzer = result['analyzer']

    # sqrt and sin should be accessible via wildcard import
    assert 'sqrt' in analyzer.names.accessible
    assert 'sin' in analyzer.names.accessible


def test_multiple_wildcard_imports():
    """Test multiple wildcard imports in the same function."""
    source = """
def func():
    from math import *
    from os import *
    return sqrt(16)
"""
    result = _analyze_names_in_function(source)
    analyzer = result['analyzer']

    # Both wildcards should be tracked (they collapse to single '*')
    assert '*' in analyzer.names.imported
    # Both packages should be tracked
    assert 'math' in analyzer.imported_packages_deep
    assert 'os' in analyzer.imported_packages_deep


def test_wildcard_in_nested_function():
    """Test that wildcard imports in nested functions don't pollute parent scope."""
    source = """
def outer():
    def inner():
        from math import *
        return sqrt(9)
    return inner()
"""
    result = _analyze_names_in_function(source)
    analyzer = result['analyzer']

    # Wildcard is in nested function, so sqrt shouldn't be in outer's local
    assert 'sqrt' not in analyzer.names.local
    # inner function name should be local to outer
    assert 'inner' in analyzer.names.local
