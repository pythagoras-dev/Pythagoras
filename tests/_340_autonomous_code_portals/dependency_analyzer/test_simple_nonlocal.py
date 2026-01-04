from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def simple_nonlocal(x):
    import math as mmm
    z =12
    def nested(y):
        nonlocal z
        return mmm.sqrt(float(y)+z)
    return nested(x)

def test_simple_nonlocal():
    assert simple_nonlocal(4) == 4
    analyzer = _analyze_names_in_function(simple_nonlocal)["analyzer"]
    assert analyzer.imported_packages_deep == {"math"}
    assert analyzer.names.accessible == {"nested", "x", "z", "mmm"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == {"mmm"}
    assert analyzer.names.local == {"nested", "x", "z"}
    assert analyzer.names.unclassified_deep == {"float"}
