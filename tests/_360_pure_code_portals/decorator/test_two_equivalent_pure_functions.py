from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure

def test_two_equivalent_pure_functions_both_with_portal(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure(portal=t.portal)
        def my_function(x:int)->int:
            return x*10

        assert my_function(x=1) == 10

        @pure(portal=t.portal)
        def my_function(x:int)->int: # comment
            """docstring"""
            return     x*10

        assert my_function(x=2) == 20

        assert t.portal.get_number_of_linked_functions() == 1



def test_two_equivalent_pure_functions_only_one_with_portal(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure(portal=t.portal)
        def my_function(x:int)->int:
            return x*10

        assert my_function(x=1) == 10
        assert my_function.linked_portal is t.portal

        @pure()
        def my_function(x:int)->int: # comment
            """docstring"""
            return     x*10

        assert my_function(x=2) == 20
        assert my_function.linked_portal is None

        assert t.portal.get_number_of_linked_functions() == 1