"""Test exception handler tracking in names_usage_analyzer.

This module tests that the analyzer correctly handles exception handlers,
particularly the distinction between bound handlers (with 'as' clause) and
unbound handlers (without 'as' clause).
"""

from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function
from pythagoras._340_autonomous_code_portals import AutonomousFn


def test_except_with_binding():
    """Test exception handler with 'as' binding is tracked as local."""
    code = """
def func():
    try:
        x = 1 / 0
    except ValueError as e:
        print(e)
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # 'e' should be in locals
    assert 'e' in analyzer.names.local, f"Expected 'e' in locals, got: {analyzer.names.local}"
    assert 'e' in analyzer.names.accessible
    # None should NOT be in any sets
    assert None not in analyzer.names.local, f"None should not be in locals, got: {analyzer.names.local}"
    assert None not in analyzer.names.accessible


def test_except_without_binding():
    """Test exception handler without 'as' binding does not add None to sets."""
    code = """
def func():
    try:
        x = 1 / 0
    except ValueError:
        pass
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # None should NOT be in any sets
    assert None not in analyzer.names.local, f"None should not be in locals, got: {analyzer.names.local}"
    assert None not in analyzer.names.accessible, f"None should not be accessible, got: {analyzer.names.accessible}"
    assert None not in analyzer.names.unclassified_deep


def test_bare_except():
    """Test bare except clause does not add None to sets."""
    code = """
def func():
    try:
        x = 1 / 0
    except:
        pass
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # None should NOT be in any sets
    assert None not in analyzer.names.local, f"None should not be in locals, got: {analyzer.names.local}"
    assert None not in analyzer.names.accessible
    assert None not in analyzer.names.unclassified_deep


def test_multiple_handlers_mixed():
    """Test multiple exception handlers, some with and some without binding."""
    code = """
def func():
    try:
        x = 1 / 0
    except ValueError as e:
        print(e)
    except TypeError:
        pass
    except KeyError as ke:
        print(ke)
    except:
        pass
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # 'e' and 'ke' should be in locals
    assert 'e' in analyzer.names.local, f"Expected 'e' in locals, got: {analyzer.names.local}"
    assert 'ke' in analyzer.names.local, f"Expected 'ke' in locals, got: {analyzer.names.local}"

    # None should NOT be in any sets
    assert None not in analyzer.names.local, f"None should not be in locals, got: {analyzer.names.local}"
    assert None not in analyzer.names.accessible
    assert None not in analyzer.names.unclassified_deep


def test_nested_try_with_mixed_handlers():
    """Test nested try blocks with mixed handler types."""
    code = """
def func():
    try:
        try:
            x = 1 / 0
        except ValueError as inner_e:
            print(inner_e)
        except TypeError:
            pass
    except Exception as outer_e:
        print(outer_e)
    except:
        pass
    return 42
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # Both bound exception names should be in locals
    assert 'inner_e' in analyzer.names.local
    assert 'outer_e' in analyzer.names.local

    # None should NOT be in any sets
    assert None not in analyzer.names.local
    assert None not in analyzer.names.accessible
    assert None not in analyzer.names.unclassified_deep


def test_autonomous_function_with_unbound_except(tmpdir):
    """Test that autonomous functions work correctly with unbound exception handlers."""
    from pythagoras._210_basic_portals.portal_tester import _PortalTester
    from pythagoras._340_autonomous_code_portals import AutonomousCodePortal

    code = """
def func():
    import sys
    try:
        x = 10 / 2
    except ValueError:
        return -1
    except ZeroDivisionError:
        return -2
    return x
"""
    # Should not raise an error about None being unclassified
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        af = AutonomousFn(code)
        result = af.execute()
        assert result == 5


def test_autonomous_function_with_bound_except(tmpdir):
    """Test that autonomous functions work correctly with bound exception handlers."""
    from pythagoras._210_basic_portals.portal_tester import _PortalTester
    from pythagoras._340_autonomous_code_portals import AutonomousCodePortal

    code = """
def func():
    import sys
    try:
        x = 10 / 2
    except ValueError as e:
        print(e)
        return -1
    return x
"""
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        af = AutonomousFn(code)
        result = af.execute()
        assert result == 5


def test_exception_name_reuse():
    """Test that exception variable can be reused in different handlers."""
    code = """
def func():
    result = 0
    try:
        x = 10 / 2
    except ValueError as e:
        print(e)
        result = 1
    except TypeError as e:
        print(e)
        result = 2
    return result
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # 'e' should be in locals (appears in both handlers, same name)
    assert 'e' in analyzer.names.local
    # None should NOT be in any sets
    assert None not in analyzer.names.local
    assert None not in analyzer.names.accessible


def test_except_with_finally():
    """Test exception handlers with finally block."""
    code = """
def func():
    try:
        x = 10 / 2
    except ValueError as e:
        print(e)
    except TypeError:
        pass
    finally:
        cleanup = True
    return x
"""
    result = _analyze_names_in_function(code)
    analyzer = result["analyzer"]

    # 'e' and 'cleanup' should be in locals
    assert 'e' in analyzer.names.local
    assert 'cleanup' in analyzer.names.local
    # None should NOT be in any sets
    assert None not in analyzer.names.local
    assert None not in analyzer.names.accessible
