"""Tests for _visit_portal functionality."""
from pythagoras import BasicPortal, PortalAwareObject, _PortalTester
from pythagoras._220_data_portals.kw_args import _visit_portal
from persidict import SafeStrTuple


class SimplePortalAware(PortalAwareObject):
    """Simple portal-aware class for testing."""

    def __init__(self, value=0, portal=None):
        super().__init__(portal)
        self.value = value

    def __getstate__(self):
        return {"value": self.value}

    def __setstate__(self, state):
        super().__setstate__(state)
        self.value = state["value"]


def test_visit_portal_with_portal_aware_object(tmpdir):
    """Test _visit_portal registers a PortalAwareObject object."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj = SimplePortalAware(42)

        # Initially not visited
        assert len(obj._visited_portals) == 0

        # Visit the portal
        _visit_portal(obj, portal)

        # Now should be registered
        assert portal in obj._visited_portals


def test_visit_portal_with_nested_dict(tmpdir):
    """Test _visit_portal traverses dictionaries and registers nested objects."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj1 = SimplePortalAware(1)
        obj2 = SimplePortalAware(2)

        data = {
            "key1": obj1,
            "key2": {
                "nested": obj2
            }
        }

        # Visit the portal with nested structure
        _visit_portal(data, portal)

        # Both objects should be registered
        assert portal in obj1._visited_portals
        assert portal in obj2._visited_portals


def test_visit_portal_with_nested_list(tmpdir):
    """Test _visit_portal traverses lists and registers nested objects."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj1 = SimplePortalAware(1)
        obj2 = SimplePortalAware(2)
        obj3 = SimplePortalAware(3)

        data = [obj1, [obj2, obj3]]

        # Visit the portal with nested structure
        _visit_portal(data, portal)

        # All objects should be registered
        assert portal in obj1._visited_portals
        assert portal in obj2._visited_portals
        assert portal in obj3._visited_portals


def test_visit_portal_with_circular_reference(tmpdir):
    """Test _visit_portal handles circular references without infinite loop."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj = SimplePortalAware(42)

        # Create circular reference
        data = {"obj": obj, "self": None}
        data["self"] = data

        # Should not crash with infinite loop
        _visit_portal(data, portal)

        # Object should still be registered
        assert portal in obj._visited_portals


def test_visit_portal_skips_strings(tmpdir):
    """Test _visit_portal skips strings (not iterable for our purposes)."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj = SimplePortalAware(42)
        data = {
            "string": "hello",
            "obj": obj
        }

        # Should not try to iterate the string
        _visit_portal(data, portal)

        # Object should be registered
        assert portal in obj._visited_portals


def test_visit_portal_skips_special_types(tmpdir):
    """Test _visit_portal skips special types like range, bytes, bytearray."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj = SimplePortalAware(42)
        data = {
            "range": range(10),
            "bytes": b"hello",
            "bytearray": bytearray(b"world"),
            "safe_str_tuple": SafeStrTuple(("a", "b")),
            "obj": obj
        }

        # Should not try to iterate these special types
        _visit_portal(data, portal)

        # Object should be registered
        assert portal in obj._visited_portals


def test_visit_portal_with_non_portal_aware_objects(tmpdir):
    """Test _visit_portal handles non-portal-aware objects gracefully."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        class RegularClass:
            def __init__(self, value):
                self.value = value

        obj = SimplePortalAware(42)
        regular = RegularClass(100)

        data = {
            "regular": regular,
            "obj": obj
        }

        # Should not crash on regular object
        _visit_portal(data, portal)

        # Only portal-aware object should be registered
        assert portal in obj._visited_portals


def test_visit_portal_with_empty_structures(tmpdir):
    """Test _visit_portal handles empty dicts and lists."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        data = {
            "empty_dict": {},
            "empty_list": [],
            "empty_tuple": ()
        }

        # Should not crash
        _visit_portal(data, portal)


def test_visit_portal_with_none(tmpdir):
    """Test _visit_portal handles None value."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        # Should not crash
        _visit_portal(None, portal)


def test_visit_portal_deep_nesting(tmpdir):
    """Test _visit_portal handles deeply nested structures."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj = SimplePortalAware(42)

        # Create deeply nested structure
        data = obj
        for _ in range(100):
            data = {"nested": data}

        # Should not crash with stack overflow
        _visit_portal(data, portal)

        # Object should be registered
        assert portal in obj._visited_portals


def test_visit_portal_with_mixed_structures(tmpdir):
    """Test _visit_portal with complex mixed structure."""
    with _PortalTester():
        portal = BasicPortal(tmpdir)

        obj1 = SimplePortalAware(1)
        obj2 = SimplePortalAware(2)
        obj3 = SimplePortalAware(3)

        data = {
            "list": [obj1, {"nested_obj": obj2}],
            "dict": {
                "key": [1, 2, 3, obj3],
                "string": "test"
            },
            "tuple": (obj1, obj2, obj3)
        }

        _visit_portal(data, portal)

        # All objects should be registered
        assert portal in obj1._visited_portals
        assert portal in obj2._visited_portals
        assert portal in obj3._visited_portals
