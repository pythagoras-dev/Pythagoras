from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *


def simple_with():
    import contextlib
    with contextlib.suppress(Exception) as suppressed:
        pass

def test_simple_with():
    simple_with()
    analyzer = analyze_names_in_function(simple_with)
    tree = analyzer["tree"]
    analyzer = analyzer["analyzer"]
    assert analyzer.imported_packages_deep == {"contextlib"}
    assert analyzer.names.accessible == {"contextlib", "Exception", "suppressed"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == {"contextlib"}
    assert analyzer.names.local == {"suppressed"}
    assert analyzer.names.unclassified_deep == {"Exception"}