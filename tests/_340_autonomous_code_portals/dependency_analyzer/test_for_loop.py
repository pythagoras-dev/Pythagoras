from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def sample_for_loop(x):
    total = 0
    for i in range(x):
        total += i
    for i,y in enumerate(range(x)):
        total += i+ y
    return total

def test_for_loop():
    sample_for_loop(3)
    dependencies = _analyze_names_in_function(sample_for_loop)
    analyzer = dependencies["analyzer"]
    assert analyzer.imported_packages_deep == set()
    assert analyzer.names.accessible == {"total","i", "x", "y", "range", "enumerate"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == set()
    assert analyzer.names.local == {"x", "i", "y", "total"}
    assert analyzer.names.unclassified_deep == {"range", "enumerate"}
