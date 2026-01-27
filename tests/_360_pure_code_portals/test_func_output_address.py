from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal,PureFnExecutionResultAddr)
from pythagoras._360_pure_code_portals.pure_decorator import pure
import pytest


def factorial(n:int) -> int:
    if n in [0, 1]:
        return 1
    else:
        return n * factorial(n=n-1)

def test_pure_factorial(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        global factorial
        factorial = pure()(factorial)

        addr_5 = PureFnExecutionResultAddr(fn=factorial, arguments=dict(n=5))

        with pytest.raises(TimeoutError):
            addr_5.get(timeout=2)

        function = addr_5.fn
        arguments = addr_5.kwargs
        name = addr_5.fn.name
        assert name == "factorial"
        assert function(**arguments) == 120



