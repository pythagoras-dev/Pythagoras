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

def test_get_cached_property_status_basic():
    """Test that _get_cached_property_status() returns correct caching status."""
    a = A()
    # Initially not cached
    assert a._get_cached_property_status("x") is False
    assert a._get_cached_property_status("y") is False

    # Cache x
    _ = a.x
    assert a._get_cached_property_status("x") is True
    assert a._get_cached_property_status("y") is False

    # Cache y
    _ = a.y
    assert a._get_cached_property_status("x") is True
    assert a._get_cached_property_status("y") is True

def test_get_cached_property_status_invalid_name():
    """Test that _get_cached_property_status() raises ValueError for invalid names."""
    a = A()

    # Non-existent property
    with pytest.raises(ValueError, match="not a cached property"):
        a._get_cached_property_status("invalid_name")

    # Regular @property (not cached_property)
    with pytest.raises(ValueError, match="not a cached property"):
        a._get_cached_property_status("z")

def test_get_cached_property_status_after_invalidation():
    """Test that _get_cached_property_status() returns False after invalidation."""
    a = A()
    _ = a.x
    _ = a.y
    assert a._get_cached_property_status("x") is True
    assert a._get_cached_property_status("y") is True

    a._invalidate_cache()
    assert a._get_cached_property_status("x") is False
    assert a._get_cached_property_status("y") is False

def test_get_cached_property_status_inheritance():
    """Test that _get_cached_property_status() works with inherited properties."""
    class Base(CacheablePropertiesMixin):
        @cached_property
        def base_prop(self):
            return "base"

    class Child(Base):
        @cached_property
        def child_prop(self):
            return "child"

    c = Child()
    assert c._get_cached_property_status("base_prop") is False
    assert c._get_cached_property_status("child_prop") is False

    _ = c.base_prop
    assert c._get_cached_property_status("base_prop") is True
    assert c._get_cached_property_status("child_prop") is False

def test_get_cached_property_status_partial():
    """Test that _get_cached_property_status() reflects partial caching correctly."""
    a = A()
    a._set_cached_properties(x=50)

    assert a._get_cached_property_status("x") is True
    assert a._get_cached_property_status("y") is False
