"""Tests for PortalAwareObject.link_to_portal() method."""
import pytest
from pythagoras import BasicPortal, PortalAwareObject, _PortalTester


class SimplePortalAware(PortalAwareObject):
    """Minimal PortalAwareObject implementation for testing."""

    def __init__(self, value=0, portal=None):
        super().__init__(portal)
        self.value = value

    def __getstate__(self):
        return {"value": self.value}

    def __setstate__(self, state):
        super().__setstate__(state)
        self.value = state["value"]


def test_link_to_portal_creates_new_instance(tmpdir):
    """Test that link_to_portal creates a new instance with different portal."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        obj1 = SimplePortalAware(42, portal=portal1)
        obj2 = obj1.link_to_portal(portal2)

        assert obj1 is not obj2
        assert obj1.value == obj2.value
        assert obj1._linked_portal is portal1
        assert obj2._linked_portal is portal2


def test_link_to_portal_returns_self_when_same_portal(tmpdir):
    """Test that link_to_portal returns self when portal is already linked."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj = SimplePortalAware(42, portal=portal)
        result = obj.link_to_portal(portal)

        assert obj is result


def test_link_to_portal_preserves_state(tmpdir):
    """Test that link_to_portal preserves object state."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        obj1 = SimplePortalAware(123, portal=portal1)
        obj2 = obj1.link_to_portal(portal2)

        assert obj2.value == 123


def test_link_to_portal_resets_visited_portals(tmpdir):
    """Test that link_to_portal resets visited portals in new instance."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        obj1 = SimplePortalAware(42, portal=portal1)

        _ = obj1.portal
        assert len(obj1._visited_portals) == 1

        obj2 = obj1.link_to_portal(portal2)

        assert len(obj2._visited_portals) == 0


def test_link_to_portal_invalid_portal_type(tmpdir):
    """Test that link_to_portal raises TypeError for non-portal argument."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)
        obj = SimplePortalAware(42, portal=portal)

        with pytest.raises(TypeError, match="portal must be a BasicPortal"):
            obj.link_to_portal("not a portal")


def test_link_to_portal_before_init_raises_error(tmpdir):
    """Test that link_to_portal before initialization raises RuntimeError."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        obj = SimplePortalAware(42, portal=portal1)

        obj._init_finished = False

        with pytest.raises(RuntimeError, match="Cannot link an uninitialized object"):
            obj.link_to_portal(portal2)


def test_link_to_portal_from_none_to_explicit(tmpdir):
    """Test linking from no portal to explicit portal."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj1 = SimplePortalAware(42)
        assert obj1._linked_portal is None

        obj2 = obj1.link_to_portal(portal)

        assert obj1 is not obj2

        assert obj2._linked_portal is portal


def test_link_to_portal_from_explicit_to_none_not_possible(tmpdir):
    """Test that link_to_portal requires a portal argument."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)
        obj = SimplePortalAware(42, portal=portal)

        with pytest.raises(TypeError):
            obj.link_to_portal(None)


def test_link_to_portal_init_finished_flag(tmpdir):
    """Test that link_to_portal sets _init_finished correctly."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        obj1 = SimplePortalAware(42, portal=portal1)
        assert obj1._init_finished

        obj2 = obj1.link_to_portal(portal2)
        assert obj2._init_finished


def test_link_to_portal_multiple_times(tmpdir):
    """Test chaining link_to_portal calls."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))
        portal3 = BasicPortal(tmpdir.mkdir("p3"))

        obj1 = SimplePortalAware(42, portal=portal1)
        obj2 = obj1.link_to_portal(portal2)
        obj3 = obj2.link_to_portal(portal3)

        assert obj1 is not obj2
        assert obj2 is not obj3
        assert obj1 is not obj3

        assert obj1._linked_portal is portal1
        assert obj2._linked_portal is portal2
        assert obj3._linked_portal is portal3


def test_link_to_portal_registration_state(tmpdir):
    """Test registration state after link_to_portal."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        obj1 = SimplePortalAware(42, portal=portal1)

        _ = obj1.portal
        assert obj1.is_registered

        obj2 = obj1.link_to_portal(portal2)

        assert not obj2.is_registered

        _ = obj2.portal
        assert obj2.is_registered


def test_link_to_portal_independent_instances(tmpdir):
    """Test that linked instances are independent."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        obj1 = SimplePortalAware(42, portal=portal1)
        obj2 = obj1.link_to_portal(portal2)

        obj1.value = 100

        assert obj2.value == 42


def test_link_to_portal_returns_correct_type(tmpdir):
    """Test that link_to_portal returns instance of same type."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))

        obj1 = SimplePortalAware(42, portal=portal1)
        obj2 = obj1.link_to_portal(portal2)

        assert type(obj1) is type(obj2)
        assert isinstance(obj2, SimplePortalAware)
