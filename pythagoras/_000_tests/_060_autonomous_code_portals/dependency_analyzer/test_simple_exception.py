from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *


def simple_exceptioms():
    try:
        pass
    except Exception as e:
        print(e)
    finally:
        a = 5

def test_simple_exceptioms():
    simple_exceptioms()
    analyzer = analyze_names_in_function(simple_exceptioms)
    tree = analyzer["tree"]
    analyzer = analyzer["analyzer"]
    assert analyzer.imported_packages_deep == set()
    assert analyzer.names.accessible == {"print", "Exception", "e", "a"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == set()
    assert analyzer.names.local == {"e", "a"}
    assert analyzer.names.unclassified_deep == {"Exception", "print"}
