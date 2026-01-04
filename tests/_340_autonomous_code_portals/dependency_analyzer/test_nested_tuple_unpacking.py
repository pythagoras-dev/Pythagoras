from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def sample_two_level_comprehension():
    """Test nested tuple unpacking in list comprehension: x, (y, z)"""
    data = [(1, (2, 3)), (4, (5, 6))]
    return [x + y + z for x, (y, z) in data]


def test_two_level_comprehension():
    """Verify that nested tuple unpacking in comprehensions works correctly."""
    sample_two_level_comprehension()
    analyzer = _analyze_names_in_function(sample_two_level_comprehension)["analyzer"]

    # In Python 3, comprehension iterator variables (x, y, z) are local to the
    # comprehension's implicit scope, NOT to the parent function.
    # Only 'data' should be in parent's local.
    assert analyzer.names.local == {"data"}

    # No variables should be flagged as unclassified (all are properly scoped)
    assert analyzer.names.unclassified_deep == set()


def sample_two_level_for_loop():
    """Test nested tuple unpacking in for-loop: x, (y, z)"""
    data = [(1, (2, 3)), (4, (5, 6))]
    result = []
    for x, (y, z) in data:
        result.append(x + y + z)
    return result


def test_two_level_for_loop():
    """Verify that nested tuple unpacking in for-loops works correctly."""
    sample_two_level_for_loop()
    analyzer = _analyze_names_in_function(sample_two_level_for_loop)["analyzer"]

    # All unpacked variables should be local
    assert "x" in analyzer.names.local
    assert "y" in analyzer.names.local
    assert "z" in analyzer.names.local
    assert "data" in analyzer.names.local
    assert "result" in analyzer.names.local

    # No nested variables should be incorrectly flagged as unclassified
    assert "y" not in analyzer.names.unclassified_deep
    assert "z" not in analyzer.names.unclassified_deep

    assert analyzer.names.local == {"x", "y", "z", "data", "result"}
    assert analyzer.names.unclassified_deep == set()


def sample_three_level_nesting():
    """Test deeply nested tuple unpacking: a, (b, (c, d))"""
    data = [(1, (2, (3, 4))), (5, (6, (7, 8)))]
    return [a + b + c + d for a, (b, (c, d)) in data]


def test_three_level_nesting():
    """Verify that deeply nested tuple unpacking works correctly."""
    sample_three_level_nesting()
    analyzer = _analyze_names_in_function(sample_three_level_nesting)["analyzer"]

    # Comprehension iterator variables are local to comprehension, not parent
    assert analyzer.names.local == {"data"}

    # No variables should be flagged as unclassified
    assert analyzer.names.unclassified_deep == set()


def sample_parallel_nested_tuples():
    """Test parallel nested tuple unpacking: (w, x), (y, z)"""
    data = [((1, 2), (3, 4)), ((5, 6), (7, 8))]
    return [w + x + y + z for (w, x), (y, z) in data]


def test_parallel_nested_tuples():
    """Verify that parallel nested tuple unpacking works correctly."""
    sample_parallel_nested_tuples()
    analyzer = _analyze_names_in_function(sample_parallel_nested_tuples)["analyzer"]

    # Comprehension iterator variables are local to comprehension, not parent
    assert analyzer.names.local == {"data"}

    # No variables should be flagged as unclassified
    assert analyzer.names.unclassified_deep == set()


def sample_dict_comprehension_nested():
    """Test nested tuple unpacking in dict comprehension."""
    data = [("a", (1, 2)), ("b", (3, 4))]
    return {key: val1 + val2 for key, (val1, val2) in data}


def test_dict_comprehension_nested():
    """Verify nested tuple unpacking in dict comprehensions."""
    sample_dict_comprehension_nested()
    analyzer = _analyze_names_in_function(sample_dict_comprehension_nested)["analyzer"]

    # Comprehension iterator variables are local to comprehension, not parent
    assert analyzer.names.local == {"data"}

    # No variables should be flagged as unclassified
    assert analyzer.names.unclassified_deep == set()


def sample_generator_expression_nested():
    """Test nested tuple unpacking in generator expression."""
    data = [(1, (2, 3)), (4, (5, 6))]
    return list(x * y * z for x, (y, z) in data)


def test_generator_expression_nested():
    """Verify nested tuple unpacking in generator expressions."""
    sample_generator_expression_nested()
    analyzer = _analyze_names_in_function(sample_generator_expression_nested)["analyzer"]

    # Generator iterator variables are local to generator, not parent
    assert analyzer.names.local == {"data"}

    # 'list' is a builtin, so it's unclassified
    assert analyzer.names.unclassified_deep == {"list"}


def sample_set_comprehension_nested():
    """Test nested tuple unpacking in set comprehension."""
    data = [(1, (2, 3)), (4, (5, 6))]
    return {x + y + z for x, (y, z) in data}


def test_set_comprehension_nested():
    """Verify nested tuple unpacking in set comprehensions."""
    sample_set_comprehension_nested()
    analyzer = _analyze_names_in_function(sample_set_comprehension_nested)["analyzer"]

    # Comprehension iterator variables are local to comprehension, not parent
    assert analyzer.names.local == {"data"}

    # No variables should be flagged as unclassified
    assert analyzer.names.unclassified_deep == set()


def sample_mixed_nesting_patterns():
    """Test multiple nested unpacking patterns in same function."""
    data1 = [(1, (2, 3)), (4, (5, 6))]
    data2 = [((7, 8), 9), ((10, 11), 12)]

    result = []
    for a, (b, c) in data1:
        result.append(a + b + c)

    for (d, e), f in data2:
        result.append(d + e + f)

    return result


def test_mixed_nesting_patterns():
    """Verify multiple different nested unpacking patterns work together."""
    sample_mixed_nesting_patterns()
    analyzer = _analyze_names_in_function(sample_mixed_nesting_patterns)["analyzer"]

    # All variables from both patterns should be local
    assert {"a", "b", "c", "d", "e", "f"}.issubset(analyzer.names.local)

    # None of the nested variables should be unclassified
    assert {"b", "c", "d", "e"}.isdisjoint(analyzer.names.unclassified_deep)

    assert analyzer.names.local == {"a", "b", "c", "d", "e", "f", "data1", "data2", "result"}
    assert analyzer.names.unclassified_deep == set()
