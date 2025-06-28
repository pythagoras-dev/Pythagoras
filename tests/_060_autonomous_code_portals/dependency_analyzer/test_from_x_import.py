from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *

def sample_from_x_import_y(x):
    from math import sqrt as sq
    from sys import api_version as apv
    from math import fabs
    y = "hehe"
    return [str(i)+y for i in [sq(x),apv,fabs(2)]]
def test_from_x_import_y_s():
    sample_from_x_import_y(3)
    analyzer = analyze_names_in_function(sample_from_x_import_y)["analyzer"]
    assert analyzer.imported_packages_deep == {"math", "sys"}
    assert analyzer.names.accessible == {"sq", "apv", "x", "y","i", "fabs", "str"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == {"sq", "apv", "fabs"}
    assert analyzer.names.local == {"x", "y","i"}
    assert analyzer.names.unclassified_deep == { "str"}
