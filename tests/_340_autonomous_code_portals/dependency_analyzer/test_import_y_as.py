from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def sample_import_y_as(a, **kwargs):
    import math
    import sys as s
    b = a + len(kwargs)
    x = math.sqrt(math.fabs(b))
    y = s.version
    return str(x) + str(y)

def test_import_y_as():
    sample_import_y_as(3, ttt=4, bbb=5)
    analyzer = _analyze_names_in_function(sample_import_y_as)["analyzer"]
    assert analyzer.names.function == "sample_import_y_as"
    assert analyzer.imported_packages_deep == {"math","sys"}
    assert analyzer.names.accessible == {"a", "kwargs", "math","s","b","x","y","len","str"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == {"math","s"}
    assert analyzer.names.local == {'kwargs', 'x', 'a', 'y', 'b'}
    assert analyzer.names.unclassified_deep == {"len","str"}

