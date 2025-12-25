"""Tests for PortalAwareClass functionality and contracts."""
import pickle
import pytest
from pythagoras import BasicPortal, PortalAwareClass, _PortalTester


class SimplePortalAware(PortalAwareClass):
    """Minimal PortalAwareClass implementation for testing."""
    
    def __init__(self, value=0, portal=None):
        super().__init__(portal)
        self.value = value
    
    def __getstate__(self):
        return {"value": self.value}
    
    def __setstate__(self, state):
        super().__setstate__(state)
        self.value = state["value"]




def test_portal_aware_init_with_none():
    """Test initialization with no portal (uses current active portal)."""
    with _PortalTester(BasicPortal) as t:
        obj = SimplePortalAware(42)
        assert obj.value == 42
        assert obj._linked_portal is None
        assert obj.portal is t.portal


def test_portal_aware_init_with_explicit_portal(tmpdir):
    """Test initialization with explicit portal binding."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal
        obj = SimplePortalAware(42, portal=portal)
        assert obj._linked_portal is portal
        assert obj.portal is portal


def test_portal_aware_init_invalid_portal_type():
    """Test that passing non-portal raises TypeError."""
    with _PortalTester():
        with pytest.raises(TypeError, match="portal must be a BasicPortal or None"):
            SimplePortalAware(portal="not a portal")


def test_portal_aware_str_id_works_after_init():
    """Test that _str_id is accessible after initialization completes."""
    with _PortalTester(BasicPortal) as t:
        obj = SimplePortalAware(42)
        # After init, _str_id should work
        str_id = obj.fingerprint
        assert str_id is not None
        assert isinstance(str_id, str)
        # Should be consistent
        assert obj.fingerprint == str_id


def test_portal_aware_registration_tracking():
    """Test that objects track portal visits and registration."""
    with _PortalTester(BasicPortal) as t:
        portal = t.portal
        obj = SimplePortalAware(10)
        
        # Object should not be registered initially
        assert len(obj._visited_portals) == 0
        assert not obj.is_registered
        
        # Access portal property to trigger registration
        _ = obj.portal
        assert len(obj._visited_portals) == 1
        assert obj.is_registered


def test_portal_aware_multiple_portal_visits(tmpdir):
    """Test object visiting multiple portals."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))
        
        obj = SimplePortalAware(20)
        
        with portal1:
            _ = obj.portal
            assert len(obj._visited_portals) == 1
        
        with portal2:
            _ = obj.portal
            assert len(obj._visited_portals) == 2


def test_portal_aware_linked_portal_stays_constant(tmpdir):
    """Test that linked portal doesn't change with context."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))
        
        with portal1:
            obj = SimplePortalAware(30, portal=portal1)
            assert obj.portal is portal1
        
        with portal2:
            # Even in different context, linked portal stays the same
            assert obj.portal is portal1


def test_portal_aware_pickle_unpickle(tmpdir):
    """Test pickling and unpickling resets portal information."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal
        obj = SimplePortalAware(100, portal=portal)
        
        # Trigger registration
        _ = obj.portal
        assert obj.is_registered
        assert len(obj._visited_portals) == 1
        
        # Pickle and unpickle
        data = pickle.dumps(obj)
        new_obj = pickle.loads(data)
        
        # Portal information should be reset
        assert new_obj.value == 100
        assert new_obj._linked_portal is None
        assert len(new_obj._visited_portals) == 0
        assert not new_obj.is_registered




def test_portal_aware_clear_method(tmpdir):
    """Test that _clear properly resets object state."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal
        obj = SimplePortalAware(50, portal=portal)
        
        # Trigger registration
        _ = obj.portal
        assert obj.is_registered
        assert obj._init_finished
        
        # Clear the object
        obj._clear()
        assert not obj._init_finished
        assert len(obj._visited_portals) == 0


def test_portal_aware_invalidate_cache():
    """Test that _invalidate_cache can be called (default is no-op)."""
    with _PortalTester(BasicPortal) as t:
        obj = SimplePortalAware(60)
        # Should not raise
        obj._invalidate_cache()


def test_portal_aware_portal_property_uses_current_active(tmpdir):
    """Test that portal property returns current active when not linked."""
    with _PortalTester():
        portal1 = BasicPortal(tmpdir.mkdir("p1"))
        portal2 = BasicPortal(tmpdir.mkdir("p2"))
        
        obj = SimplePortalAware(70)
        
        with portal1:
            assert obj.portal is portal1
        
        with portal2:
            assert obj.portal is portal2
