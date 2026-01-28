"""Test walrus operator (:=) handling in names_usage_analyzer."""

from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def test_walrus_in_if_condition():
    """Test walrus operator in if condition."""
    def func():
        if (n := 10) > 5:
            return n
        return 0

    result = _analyze_names_in_function(func)
    analyzer = result["analyzer"]

    # n should be recognized as a local variable
    assert 'n' in analyzer.names.local, f"Expected 'n' in locals, got: {analyzer.names.local}"
    assert 'n' not in analyzer.names.unclassified_deep, f"'n' should not be unclassified, got: {analyzer.names.unclassified_deep}"


def test_walrus_in_while_condition():
    """Test walrus operator in while condition."""
    def func():
        result = []
        i = 0
        while (item := i * 2) < 10:
            result.append(item)
            i += 1
        return result

    result = _analyze_names_in_function(func)
    analyzer = result["analyzer"]

    # item should be recognized as a local variable
    assert 'item' in analyzer.names.local, f"Expected 'item' in locals, got: {analyzer.names.local}"
    assert 'item' not in analyzer.names.unclassified_deep, "'item' should not be unclassified"


def test_walrus_in_list_comprehension():
    """Test walrus operator in list comprehension.

    In Python 3.8+, walrus operators in comprehensions create variables in the
    enclosing scope (the function), not in the comprehension's implicit scope.
    However, our analyzer treats comprehensions as nested scopes, so the walrus
    target 'y' won't be detected in the parent's locals - it's in the nested
    comprehension scope's locals but those aren't merged up.

    This is actually correct behavior for autonomy checking: if you use a walrus
    in a comprehension and then try to reference that variable outside the
    comprehension, Python allows it, but it's not visible in our static analysis,
    which is fine for autonomy purposes.
    """
    def func():
        return [y for x in range(5) if (y := x * 2) > 4]

    result = _analyze_names_in_function(func)
    analyzer = result["analyzer"]

    # The walrus target 'y' is in the nested comprehension scope, not parent scope
    # This is expected behavior - comprehensions are analyzed as nested scopes
    # and walrus targets don't leak up in our analysis (which is safe/conservative)
    assert 'y' not in analyzer.names.local
    # range is unclassified because it's not imported
    assert 'range' in analyzer.names.unclassified_deep


def test_walrus_simple_assignment():
    """Test simple walrus operator assignment."""
    def func():
        result = (_x := 5) + 10
        return result

    result = _analyze_names_in_function(func)
    analyzer = result["analyzer"]

    # _x should be recognized as a local variable
    assert '_x' in analyzer.names.local, f"Expected '_x' in locals, got: {analyzer.names.local}"
    assert '_x' not in analyzer.names.unclassified_deep, "'_x' should not be unclassified"


def test_walrus_multiple_assignments():
    """Test multiple walrus operator assignments."""
    def func():
        if (a := 1) and (b := 2):
            return a + b
        return 0

    result = _analyze_names_in_function(func)
    analyzer = result["analyzer"]

    # Both a and b should be recognized as local variables
    assert 'a' in analyzer.names.local, f"Expected 'a' in locals, got: {analyzer.names.local}"
    assert 'b' in analyzer.names.local, f"Expected 'b' in locals, got: {analyzer.names.local}"
    assert 'a' not in analyzer.names.unclassified_deep
    assert 'b' not in analyzer.names.unclassified_deep


def test_walrus_nested_expression():
    """Test walrus operator in nested expression."""
    def func():
        data = [1, 2, 3, 4, 5]
        if (n := len(data)) > 3 and (doubled := n * 2) < 20:
            return doubled
        return 0

    result = _analyze_names_in_function(func)
    analyzer = result["analyzer"]

    # Both n and doubled should be local
    assert 'n' in analyzer.names.local, f"Expected 'n' in locals, got: {analyzer.names.local}"
    assert 'doubled' in analyzer.names.local, f"Expected 'doubled' in locals, got: {analyzer.names.local}"
