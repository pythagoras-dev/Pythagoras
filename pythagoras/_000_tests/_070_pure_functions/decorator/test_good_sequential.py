from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._070_pure_functions.pure_core_classes import (
    PureCodePortal,PureFnExecutionResultAddr)
from pythagoras._070_pure_functions.pure_decorator import pure
from pythagoras._070_pure_functions.purity_checks import is_pure

def test_good_sequential(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure()
        def my_function(x:int)->int:
            return x*10

        assert my_function(x=1) == 10

        @pure()
        def my_function(x:int)->int: # comment
            """docstring"""
            return     x*10

        assert my_function(x=2) == 20
