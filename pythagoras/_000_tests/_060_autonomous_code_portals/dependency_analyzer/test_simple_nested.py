from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *


def simple_nested(x):
    def nested(y):
        import math
        return math.sqrt(y)
    return nested(x)

def test_simple_nested():
    assert simple_nested(4) == 2
    analyzer = analyze_names_in_function(simple_nested)["analyzer"]
    assert analyzer.imported_packages_deep == {"math"}
    assert analyzer.names.accessible == {"nested", "x"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == set()
    assert analyzer.names.local == {"nested", "x"}
    assert analyzer.names.unclassified_deep == set()
