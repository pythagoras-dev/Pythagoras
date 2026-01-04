from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure

def test_two_different_pure_functions_with_two_portal_links(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure(portal=t.portal)
        def my_function(x:int)->int:
            return x*10

        # Lazy registration - not registered yet
        assert t.portal.get_number_of_linked_functions() == 0

        # Calling function triggers registration
        assert my_function(x=1) == 10
        assert t.portal.get_number_of_linked_functions() == 1

        @pure(portal=t.portal)
        def my_function(x:int)->int: # comment
            """docstring"""
            return     x+20

        # Still only 1 function registered
        assert t.portal.get_number_of_linked_functions() == 1

        # Second function call triggers its registration
        assert my_function(x=2) == 22
        assert t.portal.get_number_of_linked_functions() == 2


def test_two_different_pure_functions_with_one_portal_link(tmpdir):
    with _PortalTester(PureCodePortal, tmpdir) as t:

        @pure(portal=t.portal)
        def my_function(x:int)->int:
            return x*10

        # Lazy registration - not registered yet
        assert t.portal.get_number_of_linked_functions() == 0

        # First function call triggers registration
        assert my_function(x=1) == 10
        assert t.portal.get_number_of_linked_functions() == 1

        @pure()
        def my_function(x:int)->int: # comment
            """docstring"""
            return     x+20

        # Still only first function registered
        assert t.portal.get_number_of_linked_functions() == 1

        # Second function has no explicit portal link, uses current active portal
        assert my_function(x=2) == 22

        # Second function doesn't link to this portal (has no explicit link)
        # so count stays at 1
        assert t.portal.get_number_of_linked_functions() == 1