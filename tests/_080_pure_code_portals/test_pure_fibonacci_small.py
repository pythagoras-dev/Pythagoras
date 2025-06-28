from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._080_pure_code_portals.pure_decorator import pure
import pytest


def fibonacci(n: int) -> int:
    if n in [0, 1]:
        return n
    else:
        return fibonacci(n=n-1) + fibonacci(n=n-2)

@pytest.mark.parametrize("p",[0, 0.5, 1])
def test_pure_fibonacci(tmpdir,p):
    # tmpdir = "YIYIYIYIYIYIYIYIYIYIYIYIYIYIYIYIY"
    with _PortalTester(PureCodePortal
            , tmpdir
            , p_consistency_checks = p) as t:
        global fibonacci
        fibonacci_decorated = pure()(fibonacci)
        for i in range(5):
            assert fibonacci_decorated(n=10) == 55

        value_store = t.portal._value_store
        assert value_store.consistency_checks_failed == 0
        if p>0:
            assert value_store.consistency_checks_attempted > 0
        else:
            assert value_store.consistency_checks_attempted == 0

        execution_results = t.portal._execution_results
        assert execution_results.consistency_checks_failed == 0
        if p>0:
            assert execution_results.consistency_checks_attempted > 0
        else:
            assert execution_results.consistency_checks_attempted == 0