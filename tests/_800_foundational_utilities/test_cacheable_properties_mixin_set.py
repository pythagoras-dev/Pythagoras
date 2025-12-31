from functools import cached_property
from pythagoras._000_foundational_utilities.cacheable_properties_mixin import CacheablePropertiesMixin
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

def test_set_cached_values_basic():
    """Test that _set_cached_values() sets values for cached properties."""
    a = A()

    a._set_cached_properties(x=100, y=200)

    # Values should be cached and accessible without computation
    assert a.__dict__["x"] == 100
    assert a.__dict__["y"] == 200
    assert a.x == 100
    assert a.y == 200

def test_set_cached_values_bypass_computation():
    """Test that _set_cached_values() bypasses property computation."""
    class Counter(CacheablePropertiesMixin):
        def __init__(self):
            self.compute_count = 0

        @cached_property
        def computed(self):
            self.compute_count += 1
            return 42

    c = Counter()
    c._set_cached_properties(computed=999)

    # Access the property - should return set value, not computed
    assert c.computed == 999
    assert c.compute_count == 0  # Never computed

def test_set_cached_values_invalid_name():
    """Test that _set_cached_values() raises ValueError for invalid names."""
    a = A()

    with pytest.raises(ValueError, match="non-cached properties"):
        a._set_cached_properties(invalid_name=123)

    # Regular property should also be rejected
    with pytest.raises(ValueError, match="non-cached properties"):
        a._set_cached_properties(z=456)

def test_set_cached_values_partial():
    """Test that _set_cached_values() can set subset of cached properties."""
    a = A()

    a._set_cached_properties(x=50)

    assert a.x == 50
    assert "y" not in a.__dict__
    assert a.y == 2  # y computes normally

def test_set_cached_values_overwrite():
    """Test that _set_cached_values() can overwrite existing cached values."""
    a = A()
    _ = a.x  # Cache original value
    assert a.x == 1

    a._set_cached_properties(x=999)

    assert a.x == 999

def test_set_cached_values_empty():
    """Test that _set_cached_values() with no arguments is safe."""
    a = A()

    a._set_cached_properties()  # Should not raise

    assert a._get_all_cached_properties() == {}

def test_set_cached_values_multiple_invalid():
    """Test that error message includes all invalid property names."""
    a = A()

    with pytest.raises(ValueError) as exc_info:
        a._set_cached_properties(invalid1=1, invalid2=2, x=3)

    error_msg = str(exc_info.value)
    assert "invalid1" in error_msg
    assert "invalid2" in error_msg

def test_get_set_cached_values_roundtrip():
    """Test that get/set cached values work together for state preservation."""
    a = A()
    # Cache some values
    _ = a.x
    _ = a.y

    # Save cached state
    saved_values = a._get_all_cached_properties()

    # Invalidate cache
    a._invalidate_cache()
    assert a._get_all_cached_properties() == {}

    # Restore cached state
    a._set_cached_properties(**saved_values)

    # Verify restoration
    assert a._get_all_cached_properties() == saved_values
    assert a.x == 1
    assert a.y == 2
