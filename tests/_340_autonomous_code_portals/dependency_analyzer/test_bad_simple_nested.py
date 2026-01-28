
import pytest

from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def bad_simple_nested(x):
    del sys  # noqa: F821
    sys.api_version  # noqa: F821
    def nested(y):
        return math.sqrt(y)  # noqa: F821
    return nested(x)

def test_bad_simple_nested():
    with pytest.raises(Exception):
        bad_simple_nested(4)
    analyzer = _analyze_names_in_function(bad_simple_nested)["analyzer"]
    assert analyzer.imported_packages_deep == set()
    assert analyzer.names.accessible == {"nested", "x", "sys"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == set()
    # 'sys' is now correctly tracked as local due to 'del sys' establishing local scope
    # (matches Python's compile-time behavior where del establishes local scope)
    assert analyzer.names.local == {"nested", "x", "sys"}
    # 'sys' is NOT in unclassified because del made it accessible before the load
    # Only 'math' remains unclassified (used in nested function without import)
    assert analyzer.names.unclassified_deep == {"math"}