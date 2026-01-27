from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure


def test_bad_sequential(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir):

        @pure()
        def my_function(x:int)->int:
            return x

        assert my_function(x=-2) == -2

        # with pytest.raises(AssertionError):
        @pure()
        def my_function(x:int)->int:
            return x*1000