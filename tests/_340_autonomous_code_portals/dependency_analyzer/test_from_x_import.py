from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function

def sample_from_x_import_y(x):
    from math import sqrt as sq
    from sys import api_version as apv
    from math import fabs
    y = "hehe"
    return [str(i)+y for i in [sq(x),apv,fabs(2)]]
def test_from_x_import_y_s():
    sample_from_x_import_y(3)
    analyzer = _analyze_names_in_function(sample_from_x_import_y)["analyzer"]
    assert analyzer.imported_packages_deep == {"math", "sys"}
    # 'i' and 'str' are local to list comprehension, not parent
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == {"sq", "apv", "fabs"}
    assert analyzer.names.local == {"x", "y"}  # 'i' is not in parent's local
    assert analyzer.names.unclassified_deep == {"str"}  # 'str' used in comprehension
