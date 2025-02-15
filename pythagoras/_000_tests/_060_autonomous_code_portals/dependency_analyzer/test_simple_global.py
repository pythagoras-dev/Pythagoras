from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *


def simple_global(x):
    import math as m
    def nested(y):
        nonlocal m
        global float
        return m.sqrt(float(y)+3*int(x))
    return nested(x)

def test_simple_global():
    assert simple_global(4) == 4
    analyzer = analyze_names_in_function(simple_global)["analyzer"]
    assert analyzer.imported_packages_deep == {"math"}
    assert analyzer.names.accessible == {"nested", "x", "m"}
    assert analyzer.names.explicitly_global_unbound_deep == {"float"}
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == {"m"}
    assert analyzer.names.local == {"nested", "x"}
    assert analyzer.names.unclassified_deep == {"int"}
