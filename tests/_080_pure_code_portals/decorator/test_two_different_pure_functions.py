from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._080_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._080_pure_code_portals.pure_decorator import pure

def test_two_different_pure_functions_with_two_portal_links(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure(portal=t.portal)
        def my_function(x:int)->int:
            return x*10

        assert my_function(x=1) == 10

        @pure(portal=t.portal)
        def my_function(x:int)->int: # comment
            """docstring"""
            return     x+20

        assert my_function(x=2) == 22

        assert t.portal.get_number_of_linked_functions() == 2


def test_two_different_pure_functions_with_one_portal_link(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure(portal=t.portal)
        def my_function(x:int)->int:
            return x*10

        assert my_function(x=1) == 10

        @pure()
        def my_function(x:int)->int: # comment
            """docstring"""
            return     x+20

        assert my_function(x=2) == 22

        assert t.portal.get_number_of_linked_functions() == 1