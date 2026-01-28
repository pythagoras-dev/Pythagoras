"""Tests for PortalAwareObject functionality and contracts."""
import pickle
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




def test_portal_aware_init_with_none():
    """Test initialization with no portal (uses current active portal)."""
    with _PortalTester(BasicPortal) as t:
        obj = SimplePortalAware(42)
        assert obj.value == 42
        assert obj.linked_portal is None
        assert obj.portal is t.portal


def test_portal_aware_init_with_explicit_portal(tmpdir):
    """Test initialization with explicit portal binding."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal
        obj = SimplePortalAware(42, portal=portal)
        assert obj.linked_portal is portal
        assert obj.portal is portal


def test_portal_aware_init_invalid_portal_type():
    """Test that passing non-portal raises TypeError."""
    with _PortalTester():
        with pytest.raises(TypeError, match="portal must be a BasicPortal or None"):
            SimplePortalAware(portal="not a portal")


def test_portal_aware_identity_key_works_after_init():
    """Test that identity_key is accessible after initialization completes."""
    with _PortalTester(BasicPortal):
        obj = SimplePortalAware(42)
        # After init, identity_key should work
        identity_key = obj.get_identity_key()
        assert identity_key is not None
        assert isinstance(identity_key, str)
        # Should be consistent
        assert obj.get_identity_key() == identity_key


def test_portal_aware_registration_tracking():
    """Test that objects track portal visits and registration."""
    with _PortalTester(BasicPortal):
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
        assert new_obj.linked_portal is None
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
    with _PortalTester(BasicPortal):
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


def test_portal_aware_identity_key_before_init_raises_error():
    """Test that accessing identity_key before initialization raises RuntimeError."""
    with _PortalTester(BasicPortal):
        # This tests the edge case where identity_key is accessed before _init_finished=True

        class TestClass(PortalAwareObject):
            def __init__(self, portal=None):
                super().__init__(portal)
                # Try to access identity_key before init is finished
                # This should raise because _init_finished is still False
                try:
                    _ = self.get_identity_key()
                    self.identity_key_accessed = True
                except RuntimeError:
                    self.identity_key_accessed = False

            def __getstate__(self):
                return {}

            def __setstate__(self, state):
                super().__setstate__(state)

        obj = TestClass()
        # The identity_key access should have failed during __init__
        assert not obj.identity_key_accessed


def test_portal_aware_first_visit_before_init_raises_error():
    """Test that _first_visit_to_portal before init raises RuntimeError."""
    with _PortalTester(BasicPortal) as t:
        portal = t.portal

        # Use SimplePortalAware which is defined at module level (can be pickled)
        obj = SimplePortalAware(42)

        # Manually set _init_finished to False to simulate not-yet-finished init
        obj._init_finished = False

        # Now try to call _first_visit_to_portal, should raise
        with pytest.raises(RuntimeError, match="Object is not fully initialized"):
            obj._first_visit_to_portal(portal)


def test_portal_aware_double_first_visit_raises_error(tmpdir):
    """Test that calling _first_visit_to_portal twice for same portal raises."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj = SimplePortalAware(100, portal=portal)

        # Verify lazy registration: portal not visited until first use
        assert portal not in obj._visited_portals

        # Trigger first visit by accessing .portal
        _ = obj.portal
        assert portal in obj._visited_portals

        # Try to visit again, should raise
        with pytest.raises(RuntimeError, match="has already been visited"):
            obj._first_visit_to_portal(portal)


def test_portal_aware_is_registered_consistency(tmpdir):
    """Test is_registered property consistency with internal state."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj = SimplePortalAware(50, portal=portal)

        # Verify lazy registration: not registered immediately after creation
        assert len(obj._visited_portals) == 0
        assert not obj.is_registered

        # Trigger registration by accessing .portal
        _ = obj.portal

        # Should be registered after first portal access
        assert len(obj._visited_portals) >= 1
        assert obj.is_registered


def test_portal_aware_abstract_getstate_not_implemented():
    """Test that PortalAwareObject without __getstate__ cannot be instantiated."""

    class IncompletePortalAware(PortalAwareObject):
        """Portal-aware class that doesn't implement __getstate__."""
        def __init__(self, portal=None):
            super().__init__(portal)

        # Missing __getstate__ implementation

        def __setstate__(self, state):
            super().__setstate__(state)

    with _PortalTester(BasicPortal):
        # Should raise TypeError when trying to instantiate
        with pytest.raises(TypeError, match="Can't instantiate abstract class.*__getstate__"):
            _obj = IncompletePortalAware()


def test_portal_aware_abstract_setstate_not_implemented():
    """Test that PortalAwareObject without __setstate__ cannot be instantiated."""

    class IncompletePortalAware2(PortalAwareObject):
        """Portal-aware class that doesn't implement __setstate__."""
        def __init__(self, portal=None):
            super().__init__(portal)

        def __getstate__(self):
            return {}

        # Missing __setstate__ implementation

    with _PortalTester(BasicPortal):
        # Should raise TypeError when trying to instantiate
        with pytest.raises(TypeError, match="Can't instantiate abstract class.*__setstate__"):
            _obj = IncompletePortalAware2()
