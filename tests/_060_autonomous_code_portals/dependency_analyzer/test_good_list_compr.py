from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *

def sample_good_list_comprecension(x):
    return [i for i in range(x)]

def test_good_list_comprencension():
    sample_good_list_comprecension(3)
    analyzer = analyze_names_in_function(sample_good_list_comprecension)["analyzer"]
    assert analyzer.imported_packages_deep == set()
    assert analyzer.names.accessible == {"i", "x", "range"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == set()
    assert analyzer.names.local == {"i", "x"}
    assert analyzer.names.unclassified_deep == {"range"}
