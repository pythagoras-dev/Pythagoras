from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def func_with_lambda(x):
    """Function with a lambda expression."""
    result = (lambda y: x + y)(5)
    return result


def test_lambda_parameters():
    """Test that lambda parameters don't leak into parent scope as unclassified."""
    result = _analyze_names_in_function(func_with_lambda)
    analyzer = result['analyzer']

    # x and result should be local
    assert 'x' in analyzer.names.local
    assert 'result' in analyzer.names.local
    # y should NOT be in unclassified (it's local to the lambda)
    assert 'y' not in analyzer.names.unclassified_deep
    # No unclassified names expected
    assert analyzer.names.unclassified_deep == set()


def func_with_multiple_lambdas(x):
    """Function with multiple lambda expressions."""
    a = (lambda y: x + y)(1)
    b = (lambda z: x + z)(2)
    c = (lambda w: x + w)(3)
    return a + b + c


def test_multiple_lambdas():
    """Test that multiple lambda parameters don't leak."""
    result = _analyze_names_in_function(func_with_multiple_lambdas)
    analyzer = result['analyzer']

    # x, a, b, c should be local
    assert analyzer.names.local == {'x', 'a', 'b', 'c'}
    # y, z, w should NOT be in unclassified
    assert 'y' not in analyzer.names.unclassified_deep
    assert 'z' not in analyzer.names.unclassified_deep
    assert 'w' not in analyzer.names.unclassified_deep
    assert analyzer.names.unclassified_deep == set()


def func_lambda_with_multiple_params(x):
    """Function with lambda that has multiple parameters."""
    result = (lambda a, b, c: x + a + b + c)(1, 2, 3)
    return result


def test_lambda_with_multiple_parameters():
    """Test that lambda with multiple parameters works correctly."""
    result = _analyze_names_in_function(func_lambda_with_multiple_params)
    analyzer = result['analyzer']

    assert 'x' in analyzer.names.local
    assert 'result' in analyzer.names.local
    # a, b, c should NOT be in unclassified
    assert 'a' not in analyzer.names.unclassified_deep
    assert 'b' not in analyzer.names.unclassified_deep
    assert 'c' not in analyzer.names.unclassified_deep
    assert analyzer.names.unclassified_deep == set()


def func_lambda_with_all_arg_types(x):
    """Function with lambda that has all argument types."""
    result = (lambda a, /, b, *args, c, **kwargs: a + b + sum(args) + c + sum(kwargs.values()))(1, 2, 3, 4, c=5, d=6)
    return result + x


def test_lambda_with_all_arg_types():
    """Test lambda with positional-only, keyword-only, *args, **kwargs."""
    result = _analyze_names_in_function(func_lambda_with_all_arg_types)
    analyzer = result['analyzer']

    assert 'x' in analyzer.names.local
    assert 'result' in analyzer.names.local
    # Lambda parameters should NOT leak
    assert 'a' not in analyzer.names.unclassified_deep
    assert 'b' not in analyzer.names.unclassified_deep
    assert 'args' not in analyzer.names.unclassified_deep
    assert 'c' not in analyzer.names.unclassified_deep
    assert 'kwargs' not in analyzer.names.unclassified_deep
    # Only 'sum' should be unclassified
    assert analyzer.names.unclassified_deep == {'sum'}


def func_nested_lambda(x):
    """Function with nested lambda expressions."""
    result = (lambda y: (lambda z: x + y + z)(3))(2)
    return result


def test_nested_lambda():
    """Test nested lambda expressions."""
    result = _analyze_names_in_function(func_nested_lambda)
    analyzer = result['analyzer']

    assert 'x' in analyzer.names.local
    assert 'result' in analyzer.names.local
    # y and z should NOT leak
    assert 'y' not in analyzer.names.unclassified_deep
    assert 'z' not in analyzer.names.unclassified_deep
    assert analyzer.names.unclassified_deep == set()


def func_lambda_uses_global():
    """Function with lambda that references an unbound name."""
    result = (lambda y: GLOBAL_VAR + y)(5)  # noqa: F821
    return result


def test_lambda_uses_global():
    """Test that lambda can reference unbound names from parent."""
    result = _analyze_names_in_function(func_lambda_uses_global)
    analyzer = result['analyzer']

    # GLOBAL_VAR should be unclassified (used but not defined)
    assert 'GLOBAL_VAR' in analyzer.names.unclassified_deep
    # y should NOT be unclassified
    assert 'y' not in analyzer.names.unclassified_deep
