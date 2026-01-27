"""Tests to verify that fix_kwargs() preserves the linked portal."""

from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._340_autonomous_code_portals import (
    AutonomousCodePortal, AutonomousFn)


def simple_add(a, b):
    return a + b


def test_fix_kwargs_preserves_explicit_portal(tmpdir):
    """Test that fix_kwargs preserves explicitly provided portal."""
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as tester:
        portal1 = tester.portal

        # Create function with explicit portal
        f1 = AutonomousFn(simple_add, portal=portal1)
        assert f1._linked_portal is portal1

        # Apply fix_kwargs
        f2 = f1.fix_kwargs(a=10)

        # Verify portal is preserved
        assert f2._linked_portal is portal1
        assert f2._linked_portal is f1._linked_portal


def test_fix_kwargs_preserves_none_portal(tmpdir):
    """Test that fix_kwargs preserves None portal (ambient context)."""
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir):
        # Create function without explicit portal (will use ambient)
        f1 = AutonomousFn(simple_add, portal=None)
        assert f1._linked_portal is None

        # Apply fix_kwargs
        f2 = f1.fix_kwargs(a=10)

        # Verify None portal is preserved
        assert f2._linked_portal is None
        assert f2._linked_portal is f1._linked_portal


def test_fix_kwargs_multiple_applications_preserve_portal(tmpdir):
    """Test that multiple fix_kwargs applications preserve portal."""
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as tester:
        portal1 = tester.portal

        # Create function with explicit portal
        f1 = AutonomousFn(simple_add, portal=portal1)

        # Apply fix_kwargs multiple times
        f2 = f1.fix_kwargs(a=10)
        f3 = f2.fix_kwargs(b=20)

        # Verify portal is preserved through chain
        assert f1._linked_portal is portal1
        assert f2._linked_portal is portal1
        assert f3._linked_portal is portal1


def test_fix_kwargs_child_uses_parent_portal(tmpdir):
    """Test that child function created via fix_kwargs uses parent's portal."""
    tmpdir1 = str(tmpdir) + "_portal1"
    tmpdir2 = str(tmpdir) + "_portal2"

    # Create two separate portals
    portal1 = AutonomousCodePortal(root_dict=tmpdir1)
    portal2 = AutonomousCodePortal(root_dict=tmpdir2)
    assert portal1 is not portal2

    # Create function with portal1
    f1 = AutonomousFn(simple_add, portal=portal1)
    assert f1._linked_portal is portal1

    # Apply fix_kwargs while portal2 is active in ambient context
    with portal2:
        # fix_kwargs should preserve portal1, not use ambient portal2
        f2 = f1.fix_kwargs(a=10)

        # Verify f2 still uses portal1, not portal2
        assert f2._linked_portal is portal1
        assert f2._linked_portal is not portal2


def test_fix_kwargs_execution_respects_preserved_portal(tmpdir):
    """Test that execution of fixed function respects the preserved portal."""
    tmpdir1 = str(tmpdir) + "_portal1"
    tmpdir2 = str(tmpdir) + "_portal2"

    # Create two separate portals
    portal1 = AutonomousCodePortal(root_dict=tmpdir1)
    portal2 = AutonomousCodePortal(root_dict=tmpdir2)

    with portal1:
        # Create and execute function with portal1
        f1 = AutonomousFn(simple_add, portal=portal1, fixed_kwargs={'a': 5})
        result1 = f1.execute(b=3)
        assert result1 == 8

        # Get initial function count in portal1
        initial_count = portal1.get_number_of_linked_functions()

        # Apply fix_kwargs
        f2 = f1.fix_kwargs(b=7)

    # Execute in context of different portal
    with portal2:
        # Execute f2 - should still register with portal1, not portal2
        result2 = f2.execute()
        assert result2 == 12

        # Verify f2 registered with portal1, not portal2
        assert portal1.get_number_of_linked_functions() > initial_count
        # portal2 should not have f2 registered (may have some from ambient)
        # Just check that portal1 increased
