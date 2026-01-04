from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def simple_deep(x):
    import math as m
    def nested(y):
        y2=y
        def subnested(z):
            global print
            nonlocal m
            return str(z+y2)
        global float
        return subnested
    def second_nested(i):
        from pandas import DataFrame
        DataFrame()
        return i*i
    return nested(x)(x)

def test_simple_deep():
    assert simple_deep(4) == "8"
    analyzer = _analyze_names_in_function(simple_deep)
    analyzer = analyzer["analyzer"]
    assert analyzer.imported_packages_deep == {"math", "pandas"}
    assert analyzer.names.accessible == {"nested","second_nested", "x", "m"}
    assert analyzer.names.explicitly_global_unbound_deep == {"float","print"}
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == {"m"}
    assert analyzer.names.local == {"nested","second_nested", "x"}
    assert analyzer.names.unclassified_deep == {"str"}
