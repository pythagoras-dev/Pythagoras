from functools import cached_property
from pythagoras._000_supporting_utilities.cacheable_properties_mixin import CacheablePropertiesMixin

class A(CacheablePropertiesMixin):
    @cached_property
    def x(self):
        return 1

    @cached_property
    def y(self):
        return 2

    @property
    def z(self):
        return 3

    def regular_method(self):
        pass

def test_get_cached_values_basic():
    """Test that _get_cached_values() returns dict with cached property values."""
    a = A()
    # Cache properties
    _ = a.x
    _ = a.y

    cached_values = a._get_all_cached_properties()

    assert isinstance(cached_values, dict)
    assert cached_values == {"x": 1, "y": 2}

def test_get_cached_values_partial():
    """Test that _get_cached_values() only includes actually cached properties."""
    a = A()
    # Cache only x, not y
    _ = a.x

    cached_values = a._get_all_cached_properties()

    assert cached_values == {"x": 1}
    assert "y" not in cached_values

def test_get_cached_values_empty():
    """Test that _get_cached_values() returns empty dict when nothing is cached."""
    a = A()

    cached_values = a._get_all_cached_properties()

    assert cached_values == {}

def test_get_cached_values_after_invalidation():
    """Test that _get_cached_values() returns empty dict after invalidation."""
    a = A()
    _ = a.x
    _ = a.y

    a._invalidate_cache()
    cached_values = a._get_all_cached_properties()

    assert cached_values == {}

def test_get_cached_values_inheritance():
    """Test that _get_cached_values() works with inherited cached properties."""
    class Base(CacheablePropertiesMixin):
        @cached_property
        def base_prop(self):
            return "base"

    class Child(Base):
        @cached_property
        def child_prop(self):
            return "child"

    c = Child()
    _ = c.base_prop
    _ = c.child_prop

    cached_values = c._get_all_cached_properties()

    assert cached_values == {"base_prop": "base", "child_prop": "child"}
