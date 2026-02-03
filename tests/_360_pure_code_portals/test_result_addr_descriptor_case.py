from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFnExecutionResultAddr)
from pythagoras._360_pure_code_portals.pure_decorator import pure
import pickle


def UpperCaseFunction(n: int) -> int:
    return n + 1


def test_result_addr_descriptor_lowercase_and_roundtrip(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):
        pure_fn = pure()(UpperCaseFunction)
        addr = PureFnExecutionResultAddr(fn=pure_fn, arguments=dict(n=2))
        assert addr.descriptor == "uppercasefunction_result_addr"

        addr_roundtrip = pickle.loads(pickle.dumps(addr))
        assert addr_roundtrip.kwargs["n"] == 2
