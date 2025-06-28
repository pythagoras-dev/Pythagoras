import sys

import pytest

from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *


def bad_simple_nested(x):
    del sys
    sys.api_version
    def nested(y):
        return math.sqrt(y)
    return nested(x)

def test_bad_simple_nested():
    with pytest.raises(Exception):
        bad_simple_nested(4)
    analyzer = analyze_names_in_function(bad_simple_nested)["analyzer"]
    assert analyzer.imported_packages_deep == set()
    assert analyzer.names.accessible == {"nested", "x", "sys"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == set()
    assert analyzer.names.local == {"nested", "x"}
    assert analyzer.names.unclassified_deep == {"math","sys"}