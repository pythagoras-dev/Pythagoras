from functools import cached_property
from pythagoras._000_supporting_utilities.cacheable_properties_mixin import CacheablePropertiesMixin
import pytest

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

def test_get_cached_property_basic():
    """Test that _get_cached_property() retrieves cached values by name."""
    a = A()
    _ = a.x
    _ = a.y

    assert a._get_cached_property("x") == 1
    assert a._get_cached_property("y") == 2

def test_get_cached_property_not_cached_yet():
    """Test that _get_cached_property() raises KeyError for uncached properties."""
    a = A()
    # x exists as a cached_property but hasn't been accessed yet
    with pytest.raises(KeyError, match="has not been computed yet"):
        a._get_cached_property("x")

    # After caching, it should work
    _ = a.x
    assert a._get_cached_property("x") == 1

def test_get_cached_property_invalid_name():
    """Test that _get_cached_property() raises ValueError for invalid names."""
    a = A()

    # Non-existent property
    with pytest.raises(ValueError, match="not a cached property"):
        a._get_cached_property("invalid_name")

    # Regular @property (not cached_property)
    with pytest.raises(ValueError, match="not a cached property"):
        a._get_cached_property("z")

def test_get_cached_property_inheritance():
    """Test that _get_cached_property() works with inherited properties."""
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

    assert c._get_cached_property("base_prop") == "base"
    assert c._get_cached_property("child_prop") == "child"

def test_get_cached_property_after_set():
    """Test that _get_cached_property() retrieves values set via _set_cached_properties()."""
    a = A()
    a._set_cached_properties(x=100, y=200)

    assert a._get_cached_property("x") == 100
    assert a._get_cached_property("y") == 200
