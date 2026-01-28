"""Tests for comprehension scope isolation (Python 3 semantics).

In Python 3, comprehensions (list, set, dict, generator) create implicit function
scopes. Iterator variables should NOT leak to the parent function scope.
"""

from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def false_negative_list_comp(n):
    """
    In Python 3: [i for i in range(n)] creates 'i' local to comprehension.
    The final 'i' refers to outer scope (undefined) -> NameError at runtime.

    The analyzer should flag this as non-autonomous.
    """
    return [i for i in range(n)], i  # noqa: F821 - Second 'i' is undefined!


def test_false_negative_list_comp():
    """Test that iterator variable doesn't leak from list comprehension."""
    # Verify Python 3 runtime behavior
    try:
        false_negative_list_comp(5)
        assert False, "Should raise NameError in Python 3"
    except NameError:
        pass  # Expected

    # Verify analyzer detects this
    analyzer = _analyze_names_in_function(false_negative_list_comp)["analyzer"]

    # 'i' should NOT be in local (it's local to comprehension only)
    # The second 'i' should be flagged as unclassified
    assert 'i' in analyzer.names.unclassified_deep, \
        f"Iterator 'i' leaked to parent scope. Local: {analyzer.names.local}, Unclassified: {analyzer.names.unclassified_deep}"


def false_negative_generator_exp(n):
    """Generator expressions should also isolate their scope."""
    return sum(i for i in range(n)), i  # noqa: F821


def test_false_negative_generator_exp():
    """Test that iterator variable doesn't leak from generator expression."""
    try:
        false_negative_generator_exp(5)
        assert False, "Should raise NameError in Python 3"
    except NameError:
        pass

    analyzer = _analyze_names_in_function(false_negative_generator_exp)["analyzer"]
    assert 'i' in analyzer.names.unclassified_deep, \
        "Iterator 'i' should not leak from generator expression"


def false_negative_set_comp(n):
    """Set comprehensions should also isolate their scope."""
    return {i for i in range(n)}, i  # noqa: F821


def test_false_negative_set_comp():
    """Test that iterator variable doesn't leak from set comprehension."""
    try:
        false_negative_set_comp(5)
        assert False, "Should raise NameError in Python 3"
    except NameError:
        pass

    analyzer = _analyze_names_in_function(false_negative_set_comp)["analyzer"]
    assert 'i' in analyzer.names.unclassified_deep, \
        "Iterator 'i' should not leak from set comprehension"


def false_negative_dict_comp(n):
    """Dict comprehensions should also isolate their scope."""
    return {i: i*2 for i in range(n)}, i  # noqa: F821


def test_false_negative_dict_comp():
    """Test that iterator variable doesn't leak from dict comprehension."""
    try:
        false_negative_dict_comp(5)
        assert False, "Should raise NameError in Python 3"
    except NameError:
        pass

    analyzer = _analyze_names_in_function(false_negative_dict_comp)["analyzer"]
    assert 'i' in analyzer.names.unclassified_deep, \
        "Iterator 'i' should not leak from dict comprehension"


def correct_usage_with_outer_i(n):
    """When 'i' is defined in parent scope, it should be accessible."""
    i = 100
    return [i for i in range(n)], i  # Second 'i' refers to outer i=100


def test_correct_usage():
    """Test that outer scope variables ARE accessible in comprehensions."""
    result = correct_usage_with_outer_i(5)
    assert result == ([0, 1, 2, 3, 4], 100)

    analyzer = _analyze_names_in_function(correct_usage_with_outer_i)["analyzer"]
    assert 'i' in analyzer.names.local
    assert 'i' not in analyzer.names.unclassified_deep


def comprehension_uses_outer_variable(n):
    """Comprehension accessing outer scope variable (not iterator)."""
    multiplier = 10
    return [i * multiplier for i in range(n)]


def test_comprehension_accesses_outer():
    """Test that comprehensions CAN access outer scope variables."""
    result = comprehension_uses_outer_variable(3)
    assert result == [0, 10, 20]

    analyzer = _analyze_names_in_function(comprehension_uses_outer_variable)["analyzer"]
    assert 'multiplier' in analyzer.names.local
    assert 'multiplier' not in analyzer.names.unclassified_deep
    # 'i' should NOT be in parent's local
    assert 'i' not in analyzer.names.local or 'i' in analyzer.names.unclassified_deep, \
        "Iterator 'i' should not leak to parent scope"


def nested_comprehensions(n):
    """Nested comprehensions with different iterator variables."""
    return [[j for j in range(i)] for i in range(n)]


def test_nested_comprehensions():
    """Test that nested comprehension iterators don't leak."""
    result = nested_comprehensions(3)
    assert result == [[], [0], [0, 1]]

    analyzer = _analyze_names_in_function(nested_comprehensions)["analyzer"]
    # Neither 'i' nor 'j' should be in parent's local
    assert 'i' not in analyzer.names.local or 'i' in analyzer.names.unclassified_deep
    assert 'j' not in analyzer.names.local or 'j' in analyzer.names.unclassified_deep


def example_from_issue(n):
    """The exact example from the issue statement."""
    return sum(i*x for i in range(n))  # noqa: F821 - x is external


def test_example_from_issue():
    """Test the exact example: should detect 'x' as external."""
    analyzer = _analyze_names_in_function(example_from_issue)["analyzer"]

    # 'x' should be flagged as unclassified (external)
    assert 'x' in analyzer.names.unclassified_deep, \
        f"'x' should be flagged as external. Unclassified: {analyzer.names.unclassified_deep}"

    # 'i' should NOT be in parent's local
    assert 'i' not in analyzer.names.local, \
        f"Iterator 'i' should not leak to parent. Local: {analyzer.names.local}"
