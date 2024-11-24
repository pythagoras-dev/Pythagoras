from pythagoras._060_autonomous_functions.names_usage_analyzer import *


def simple_nested_2(x):
    import math
    def nested(y):
        return math.sqrt(float(y))
    return nested(x)

def test_simple_nested_2():
    assert simple_nested_2(4) == 2
    analyzer = analyze_names_in_function(simple_nested_2)["analyzer"]
    assert analyzer.imported_packages_deep == {"math"}
    assert analyzer.names.accessible == {"nested", "x", "math"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == {"math"}
    assert analyzer.names.local == {"nested", "x"}
    assert analyzer.names.unclassified_deep == {"float"}
