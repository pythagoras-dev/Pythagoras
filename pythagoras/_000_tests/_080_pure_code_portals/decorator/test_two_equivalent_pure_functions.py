from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal,PureFnExecutionResultAddr)
from pythagoras._080_pure_code_portals.pure_decorator import pure

def test_two_equivalent_pure_functions(tmpdir):
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

        assert len(t.portal.known_functions) == 1
