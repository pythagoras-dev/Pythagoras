"""Tests for edge cases in autonomous functions."""

from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._340_autonomous_code_portals import *


def test_empty_autonomous_function():
    """Test that an autonomous function with only pass statement works."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def do_nothing():
            pass

        # Should execute without error and return None
        result = do_nothing.execute()
        assert result is None


def test_autonomous_function_with_only_docstring():
    """Test that an autonomous function with only a docstring works."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def documented():
            """This function does nothing but has a docstring."""
            pass

        result = documented.execute()
        assert result is None


def test_autonomous_function_returning_none_explicitly():
    """Test autonomous function that explicitly returns None."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def return_none():
            return None

        result = return_none.execute()
        assert result is None


def test_autonomous_function_with_multiple_return_statements():
    """Test autonomous function with multiple return paths."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def conditional_return(x):
            if x > 0:
                return "positive"
            elif x < 0:
                return "negative"
            else:
                return "zero"

        assert conditional_return.execute(x=5) == "positive"
        assert conditional_return.execute(x=-3) == "negative"
        assert conditional_return.execute(x=0) == "zero"


def test_autonomous_function_with_only_literals():
    """Test autonomous function that only uses literals."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def return_constants():
            return [1, 2, 3, "hello", True, None]

        result = return_constants.execute()
        assert result == [1, 2, 3, "hello", True, None]


def test_autonomous_function_with_builtin_types():
    """Test autonomous function using only builtin type constructors."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def use_builtins(x):
            return {
                'int': int(x),
                'float': float(x),
                'str': str(x),
                'list': list(range(x)),
                'tuple': tuple([x, x+1]),
                'set': set([x]),
                'dict': dict(a=x)
            }

        result = use_builtins.execute(x=3)
        assert result['int'] == 3
        assert result['float'] == 3.0
        assert result['str'] == '3'
        assert result['list'] == [0, 1, 2]
        assert result['tuple'] == (3, 4)
        assert result['set'] == {3}
        assert result['dict'] == {'a': 3}


def test_autonomous_function_single_expression():
    """Test autonomous function with single expression (no statements)."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def triple(x):
            return x * 3

        assert triple.execute(x=10) == 30


def test_autonomous_function_with_all_builtin_collections():
    """Test autonomous function creating all built-in collection types."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def make_collections(n):
            return {
                'list': [i for i in range(n)],
                'tuple': tuple(range(n)),
                'set': {i for i in range(n)},
                'dict': {i: i**2 for i in range(n)},
                'frozenset': frozenset(range(n))
            }

        result = make_collections.execute(n=3)
        assert result['list'] == [0, 1, 2]
        assert result['tuple'] == (0, 1, 2)
        assert result['set'] == {0, 1, 2}
        assert result['dict'] == {0: 0, 1: 1, 2: 4}
        assert result['frozenset'] == frozenset({0, 1, 2})
