from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *


def nested_yeld(x):
    def nested(y):
        y2=y
        def subnested(z):
            global print
            yield str(z+y2)
        global float
        return subnested
    def second_nested(i):
        from pandas import DataFrame
        DataFrame()
        return i*i
    return nested(x)(x)

def test_nested_yeld():
    analyzer = analyze_names_in_function(nested_yeld)
    tree = analyzer["tree"]
    analyzer = analyzer["analyzer"]
    assert analyzer.n_yelds == 0
