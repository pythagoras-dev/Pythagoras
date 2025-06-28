
import pytest

from pythagoras._060_autonomous_code_portals.names_usage_analyzer import *



def sample_bad_list_comprecension(x):
    n = i
    return [i+n for i in range(x)]

def test_bad_list_comprencension():
    with pytest.raises(Exception):
        sample_bad_list_comprecension(3)
    analyzer = analyze_names_in_function(sample_bad_list_comprecension)["analyzer"]
    assert analyzer.imported_packages_deep == set()
    assert analyzer.names.accessible == {"i", "x", "range", "n"}
    assert analyzer.names.explicitly_global_unbound_deep == set()
    assert analyzer.names.explicitly_nonlocal_unbound_deep == set()
    assert analyzer.names.imported == set()
    assert analyzer.names.local == {"x", "n"}
    assert analyzer.names.unclassified_deep == {"range","i"}
