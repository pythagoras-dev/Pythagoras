"""Tests for BasicPortal linked objects functionality."""
from pythagoras import BasicPortal, PortalAwareObject, _PortalTester


class TypeA(PortalAwareObject):
    """Test class of type A."""
    
    def __init__(self, value, portal=None):
        super().__init__(portal)
        self.value = value
    
    def __getstate__(self):
        return {"value": self.value}
    
    def __setstate__(self, state):
        super().__setstate__(state)
        self.value = state["value"]


class TypeB(PortalAwareObject):
    """Test class of type B."""
    
    def __init__(self, value, portal=None):
        super().__init__(portal)
        self.value = value
    
    def __getstate__(self):
        return {"value": self.value}
    
    def __setstate__(self, state):
        super().__setstate__(state)
        self.value = state["value"]


def test_get_linked_objects_returns_set(tmpdir):
    """Verify get_linked_objects returns a set, not a list."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal

        # Empty portal returns empty set
        result = portal.get_linked_objects()
        assert isinstance(result, set)
        assert len(result) == 0

        # With objects, still returns set
        obj = TypeA(1, portal)
        _ = obj.portal
        result = portal.get_linked_objects()
        assert isinstance(result, set)
        assert obj in result


def test_get_linked_objects_no_filter(tmpdir):
    """Test getting all linked objects without type filtering."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal

        obj_a1 = TypeA(1, portal)
        obj_a2 = TypeA(2, portal)
        obj_b1 = TypeB(3, portal)

        # Verify lazy registration: objects not registered until first use
        assert portal.count_linked_objects() == 0

        # Trigger registration by accessing .portal
        _ = obj_a1.portal
        _ = obj_a2.portal
        _ = obj_b1.portal

        # Now objects should be registered
        assert portal.count_linked_objects() == 3

        linked = portal.get_linked_objects()
        assert len(linked) == 3
        assert obj_a1 in linked
        assert obj_a2 in linked
        assert obj_b1 in linked


def test_get_linked_objects_with_type_filter(tmpdir):
    """Test getting linked objects filtered by type."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal

        obj_a1 = TypeA(1, portal)
        obj_a2 = TypeA(2, portal)
        obj_b1 = TypeB(3, portal)

        # Verify lazy registration: objects not registered until first use
        assert portal.count_linked_objects() == 0

        # Trigger registration by accessing .portal
        _ = obj_a1.portal
        _ = obj_a2.portal
        _ = obj_b1.portal

        # Now objects should be registered
        linked_a = portal.get_linked_objects(target_class=TypeA)
        assert len(linked_a) == 2
        assert obj_a1 in linked_a
        assert obj_a2 in linked_a
        assert obj_b1 not in linked_a

        linked_b = portal.get_linked_objects(target_class=TypeB)
        assert len(linked_b) == 1
        assert obj_b1 in linked_b


def test_get_number_of_linked_objects_no_filter(tmpdir):
    """Test counting all linked objects without type filtering."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal

        assert portal.count_linked_objects() == 0

        # Verify lazy registration for first object
        obj1 = TypeA(1, portal)
        assert portal.count_linked_objects() == 0  # Not registered yet
        _ = obj1.portal  # Trigger registration
        assert portal.count_linked_objects() == 1  # Now registered

        # Verify lazy registration for second object
        obj2 = TypeA(2, portal)
        assert portal.count_linked_objects() == 1  # Still only first registered
        _ = obj2.portal  # Trigger registration
        assert portal.count_linked_objects() == 2  # Now both registered

        # Verify lazy registration for third object
        obj3 = TypeB(3, portal)
        assert portal.count_linked_objects() == 2  # Still only first two registered
        _ = obj3.portal  # Trigger registration
        assert portal.count_linked_objects() == 3  # All three registered


def test_get_number_of_linked_objects_with_type_filter(tmpdir):
    """Test counting linked objects filtered by type."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal

        obj_a1 = TypeA(1, portal)
        obj_a2 = TypeA(2, portal)
        obj_b1 = TypeB(3, portal)

        # Verify lazy registration: objects not registered until first use
        assert portal.count_linked_objects(target_class=TypeA) == 0
        assert portal.count_linked_objects(target_class=TypeB) == 0

        # Trigger registration by accessing .portal
        _ = obj_a1.portal
        _ = obj_a2.portal
        _ = obj_b1.portal

        # Now objects should be registered
        assert portal.count_linked_objects(target_class=TypeA) == 2
        assert portal.count_linked_objects(target_class=TypeB) == 1


def test_entropy_infuser_property(tmpdir):
    """Test that entropy_infuser property returns a random.Random instance."""
    with _PortalTester(BasicPortal, root_dict=str(tmpdir)) as t:
        portal = t.portal
        
        infuser = portal.entropy_infuser
        assert infuser is not None
        
        # Should be a Random instance
        import random
        assert isinstance(infuser, random.Random)
        
        # Should be consistent (same instance)
        assert portal.entropy_infuser is infuser
        
        # Should be able to generate random numbers
        val1 = infuser.random()
        val2 = infuser.random()
        assert 0 <= val1 <= 1
        assert 0 <= val2 <= 1
