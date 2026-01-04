from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def simple_yeld(x):
    y = x+2
    if y > 100:
        yield y
    else:
        yield x

def test_simple_yeld():
    analyzer = _analyze_names_in_function(simple_yeld)
    analyzer = analyzer["analyzer"]
    assert analyzer.n_yelds == 2
