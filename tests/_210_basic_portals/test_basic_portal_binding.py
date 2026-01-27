"""Tests for PortalAwareObject portal binding behavior."""
import pytest
from pythagoras import BasicPortal, _PortalTester, PortalAwareObject


class SimplePortalAware(PortalAwareObject):
    """Minimal PortalAwareObject implementation for testing."""

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        super().__setstate__(state)


def test_basic_portal_lazy_binding(tmpdir):
    """Verify unlinked objects use current portal lazily."""
    with _PortalTester(BasicPortal, root_dict = str(tmpdir)) as t:
        portal = t.portal
        obj = SimplePortalAware()
        assert obj.linked_portal is None
        assert obj.portal is portal
        assert obj.linked_portal is None

def test_basic_portal_explicit_binding(tmpdir):
    """Verify explicitly linked objects always use their linked portal."""
    with _PortalTester(BasicPortal, root_dict = str(tmpdir)) as t:
        portal = t.portal
        obj = SimplePortalAware(portal)
        assert obj.linked_portal is portal
        assert obj.portal is portal
        assert obj.linked_portal is portal

def test_basic_portal_cannot_set_portal(tmpdir):
    """Verify portal property is read-only."""
    with _PortalTester(BasicPortal, root_dict = str(tmpdir)) as t:
        portal = t.portal
        obj = SimplePortalAware()
        with pytest.raises(AttributeError):
            obj.portal = portal