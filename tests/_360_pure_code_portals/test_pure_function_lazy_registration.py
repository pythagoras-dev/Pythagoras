"""Comprehensive tests for lazy registration of pure functions.

This module explicitly tests and documents the lazy registration behavior
of pure functions, ensuring they are only registered with their portal
on first use (either via .portal access or function execution), not during
creation.
"""

from pythagoras import PureCodePortal, pure, _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import PureFn


def sample_function(x: int) -> int:
    """Sample function for testing."""
    return x * 10


def another_function(a: int, b: int) -> int:
    """Another sample function."""
    return a + b


def test_pure_fn_not_registered_on_creation(tmpdir):
    """Test that PureFn objects are not registered immediately after creation."""
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal

        # Initial state: no functions registered
        assert portal.get_number_of_linked_functions() == 0

        # Create PureFn with explicit portal - should NOT register yet (lazy)
        pure_fn = PureFn(sample_function, portal=portal)
        assert portal.get_number_of_linked_functions() == 0

        # Verify object exists and has portal link
        assert pure_fn._linked_portal is portal
        assert len(pure_fn._visited_portals) == 0  # Not visited yet


def test_pure_fn_registered_on_portal_access(tmpdir):
    """Test that accessing .portal triggers lazy registration."""
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal

        pure_fn = PureFn(sample_function, portal=portal)
        assert portal.get_number_of_linked_functions() == 0

        # Access .portal property - should trigger registration
        accessed_portal = pure_fn.portal
        assert accessed_portal is portal
        assert portal.get_number_of_linked_functions() == 1
        assert len(pure_fn._visited_portals) == 1
        assert portal in pure_fn._visited_portals


def test_pure_fn_registered_on_function_call(tmpdir):
    """Test that calling a pure function triggers lazy registration."""
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal

        pure_fn = PureFn(sample_function, portal=portal)
        assert portal.get_number_of_linked_functions() == 0

        # Call the function - should trigger registration
        result = pure_fn(x=5)
        assert result == 50
        assert portal.get_number_of_linked_functions() == 1
        assert len(pure_fn._visited_portals) == 1


def test_pure_decorator_lazy_registration(tmpdir):
    """Test lazy registration with @pure decorator."""
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal

        # Decorator with explicit portal
        @pure(portal=portal)
        def decorated_func(n: int) -> int:
            return n ** 2

        # Not registered yet
        assert portal.get_number_of_linked_functions() == 0

        # Call the function
        result = decorated_func(n=4)
        assert result == 16

        # Now registered
        assert portal.get_number_of_linked_functions() == 1


def test_multiple_pure_functions_lazy_registration(tmpdir):
    """Test lazy registration with multiple pure functions."""
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal

        # Create three pure functions
        fn1 = PureFn(sample_function, portal=portal)
        fn2 = PureFn(another_function, portal=portal)

        @pure(portal=portal)
        def fn3(x: int) -> int:
            return x - 5

        # None registered yet
        assert portal.get_number_of_linked_functions() == 0

        # Trigger registration one by one
        _ = fn1.portal
        assert portal.get_number_of_linked_functions() == 1

        result2 = fn2(a=10, b=20)  # Call triggers registration
        assert result2 == 30
        assert portal.get_number_of_linked_functions() == 2

        result3 = fn3(x=15)  # Call triggers registration
        assert result3 == 10
        assert portal.get_number_of_linked_functions() == 3


def test_pure_function_without_explicit_portal(tmpdir):
    """Test pure function without explicit portal uses current active portal."""
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal

        # Create without explicit portal
        pure_fn = PureFn(sample_function)

        # No explicit link
        assert pure_fn._linked_portal is None

        # Not registered in any portal yet (no explicit link)
        assert portal.get_number_of_linked_functions() == 0

        # Call function - uses current active portal
        result = pure_fn(x=3)
        assert result == 30

        # Function uses the portal but isn't tracked as "linked"
        # (only functions with explicit portal= link are tracked)
        assert portal.get_number_of_linked_functions() == 0

        # But the function does access the portal successfully
        assert pure_fn.portal is portal


def test_lazy_registration_idempotent(tmpdir):
    """Test that registration only happens once per portal."""
    with _PortalTester(PureCodePortal, tmpdir) as t:
        portal = t.portal

        pure_fn = PureFn(sample_function, portal=portal)

        # Trigger registration multiple times
        _ = pure_fn.portal
        _ = pure_fn.portal
        pure_fn(x=2)
        pure_fn(x=3)

        # Still only registered once
        assert portal.get_number_of_linked_functions() == 1
        assert len(pure_fn._visited_portals) == 1


def test_lazy_registration_with_multiple_portals(tmpdir):
    """Test object visiting multiple portals lazily."""
    with _PortalTester():
        portal1 = PureCodePortal(tmpdir.mkdir("p1"))
        portal2 = PureCodePortal(tmpdir.mkdir("p2"))

        # Function with explicit link to portal1
        pure_fn = PureFn(sample_function, portal=portal1)

        # Not registered in either portal yet
        assert portal1.get_number_of_linked_functions() == 0
        assert portal2.get_number_of_linked_functions() == 0

        # Call with portal1 active
        with portal1:
            result = pure_fn(x=4)
            assert result == 40
            assert portal1.get_number_of_linked_functions() == 1
            assert len(pure_fn._visited_portals) == 1

        # Access from portal2 context
        with portal2:
            # Still linked to portal1, not portal2
            accessed_portal = pure_fn.portal
            assert accessed_portal is portal1
            # portal1 still has 1, portal2 has 0
            assert portal1.get_number_of_linked_functions() == 1
            assert portal2.get_number_of_linked_functions() == 0
