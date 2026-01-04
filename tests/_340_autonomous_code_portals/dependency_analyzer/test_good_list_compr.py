from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function

def sample_good_list_comprecension(x):
    return [i for i in range(x)]

def test_good_list_comprencension():
    sample_good_list_comprecension(3)
    analyzer = _analyze_names_in_function(sample_good_list_comprecension)["analyzer"]
    assert analyzer.imported_packages_deep == set()
    # In Python 3, 'i' is local to comprehension, not parent
    # Only 'x' is accessible in parent scope
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == set()
    assert analyzer.names.local == {"x"}  # 'i' is not in parent's local
    assert analyzer.names.unclassified_deep == {"range"}
