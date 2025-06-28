from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *


def simple_yeld(x):
    y = x+2
    if y > 100:
        yield y
    else:
        yield x

def test_simple_yeld():
    analyzer = analyze_names_in_function(simple_yeld)
    tree = analyzer["tree"]
    analyzer = analyzer["analyzer"]
    assert analyzer.n_yelds == 2
