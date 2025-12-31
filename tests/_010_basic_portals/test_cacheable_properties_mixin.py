"""Tests for CacheablePropertiesMixin functionality."""

import pytest
from functools import cached_property
from pythagoras._000_supporting_utilities.cacheable_properties_mixin import (
    CacheablePropertiesMixin
)


class SimpleCacheable(CacheablePropertiesMixin):
    """Minimal class with cached properties for testing."""

    def __init__(self, value):
        self.value = value
        self.compute_count = 0

    @cached_property
    def cached_prop1(self):
        """First cached property."""
        self.compute_count += 1
        return self.value * 2

    @cached_property
    def cached_prop2(self):
        """Second cached property."""
        return self.value * 3


class CacheableWithSlots(CacheablePropertiesMixin):
    """Class with __slots__ including __dict__."""
    __slots__ = ('value', '__dict__')

    def __init__(self, value):
        self.value = value

    @cached_property
    def cached_prop(self):
        return self.value * 2


class CacheableWithSlotsNoDict(CacheablePropertiesMixin):
    """Class with __slots__ but no __dict__ - should fail."""
    __slots__ = ('value',)

    def __init__(self, value):
        self.value = value

    @cached_property
    def cached_prop(self):
        return self.value * 2


def test_all_cached_properties_names_discovery():
    """Test discovery of all cached property names."""
    obj = SimpleCacheable(10)

    names = obj._all_cached_properties_names
    assert isinstance(names, frozenset)
    assert len(names) == 2
    assert 'cached_prop1' in names
    assert 'cached_prop2' in names


def test_all_cached_properties_names_is_cached():
    """Test that property names discovery is cached."""
    obj = SimpleCacheable(10)

    names1 = obj._all_cached_properties_names
    names2 = obj._all_cached_properties_names

    # Should return the same object (cached)
    assert names1 is names2


def test_get_all_cached_properties_status_none_computed():
    """Test status when no cached properties have been computed."""
    obj = SimpleCacheable(10)

    status = obj._get_all_cached_properties_status()

    assert isinstance(status, dict)
    assert len(status) == 2
    assert status['cached_prop1'] is False
    assert status['cached_prop2'] is False


def test_get_all_cached_properties_status_some_computed():
    """Test status when some cached properties have been computed."""
    obj = SimpleCacheable(10)

    # Access one property to trigger computation
    _ = obj.cached_prop1

    status = obj._get_all_cached_properties_status()

    assert status['cached_prop1'] is True
    assert status['cached_prop2'] is False


def test_get_all_cached_properties_status_all_computed():
    """Test status when all cached properties have been computed."""
    obj = SimpleCacheable(10)

    # Access both properties
    _ = obj.cached_prop1
    _ = obj.cached_prop2

    status = obj._get_all_cached_properties_status()

    assert status['cached_prop1'] is True
    assert status['cached_prop2'] is True


def test_get_all_cached_properties_empty():
    """Test retrieving cached values when none are computed."""
    obj = SimpleCacheable(10)

    cached = obj._get_all_cached_properties()

    assert isinstance(cached, dict)
    assert len(cached) == 0


def test_get_all_cached_properties_some_computed():
    """Test retrieving only computed cached values."""
    obj = SimpleCacheable(10)

    # Compute one property
    result1 = obj.cached_prop1

    cached = obj._get_all_cached_properties()

    assert len(cached) == 1
    assert 'cached_prop1' in cached
    assert cached['cached_prop1'] == result1
    assert 'cached_prop2' not in cached


def test_get_all_cached_properties_all_computed():
    """Test retrieving all computed cached values."""
    obj = SimpleCacheable(10)

    result1 = obj.cached_prop1
    result2 = obj.cached_prop2

    cached = obj._get_all_cached_properties()

    assert len(cached) == 2
    assert cached['cached_prop1'] == result1
    assert cached['cached_prop2'] == result2


def test_get_cached_property_success():
    """Test retrieving a specific cached property value."""
    obj = SimpleCacheable(10)

    # Compute the property
    expected = obj.cached_prop1

    # Retrieve it
    result = obj._get_cached_property('cached_prop1')

    assert result == expected
    assert result == 20


def test_get_cached_property_invalid_name():
    """Test ValueError when name is not a cached property."""
    obj = SimpleCacheable(10)

    with pytest.raises(ValueError, match="not a cached property"):
        obj._get_cached_property('nonexistent')


def test_get_cached_property_not_computed():
    """Test KeyError when property exists but not yet computed."""
    obj = SimpleCacheable(10)

    with pytest.raises(KeyError, match="has not been computed yet"):
        obj._get_cached_property('cached_prop1')


def test_get_cached_property_status_success():
    """Test checking status of a specific cached property."""
    obj = SimpleCacheable(10)

    # Before computation
    assert obj._get_cached_property_status('cached_prop1') is False

    # After computation
    _ = obj.cached_prop1
    assert obj._get_cached_property_status('cached_prop1') is True


def test_get_cached_property_status_invalid_name():
    """Test ValueError when checking status of invalid property name."""
    obj = SimpleCacheable(10)

    with pytest.raises(ValueError, match="not a cached property"):
        obj._get_cached_property_status('nonexistent')


def test_set_cached_properties_single():
    """Test directly setting a single cached property value."""
    obj = SimpleCacheable(10)

    # Set without computing
    obj._set_cached_properties(cached_prop1=999)

    # Should return the set value without computation
    assert obj.compute_count == 0
    assert obj.cached_prop1 == 999
    assert obj.compute_count == 0  # Still not computed


def test_set_cached_properties_multiple():
    """Test directly setting multiple cached property values."""
    obj = SimpleCacheable(10)

    obj._set_cached_properties(cached_prop1=100, cached_prop2=200)

    assert obj.cached_prop1 == 100
    assert obj.cached_prop2 == 200


def test_set_cached_properties_invalid_name():
    """Test ValueError when setting non-cached property."""
    obj = SimpleCacheable(10)

    with pytest.raises(ValueError, match="non-cached properties"):
        obj._set_cached_properties(nonexistent=123)


def test_set_cached_properties_mixed_valid_invalid():
    """Test ValueError when mixing valid and invalid property names."""
    obj = SimpleCacheable(10)

    with pytest.raises(ValueError, match="non-cached properties"):
        obj._set_cached_properties(cached_prop1=100, invalid=200)


def test_invalidate_cache_clears_all():
    """Test that invalidate_cache clears all cached values."""
    obj = SimpleCacheable(10)

    # Compute both properties
    _ = obj.cached_prop1
    _ = obj.cached_prop2

    # Verify they're cached
    status_before = obj._get_all_cached_properties_status()
    assert status_before['cached_prop1'] is True
    assert status_before['cached_prop2'] is True

    # Invalidate
    obj._invalidate_cache()

    # Verify they're cleared
    status_after = obj._get_all_cached_properties_status()
    assert status_after['cached_prop1'] is False
    assert status_after['cached_prop2'] is False


def test_invalidate_cache_forces_recomputation():
    """Test that invalidate_cache forces properties to recompute."""
    obj = SimpleCacheable(10)

    # First computation
    result1 = obj.cached_prop1
    count_after_first = obj.compute_count
    assert count_after_first == 1

    # Access again (should not recompute)
    result2 = obj.cached_prop1
    assert result2 == result1
    assert obj.compute_count == 1

    # Invalidate
    obj._invalidate_cache()

    # Access again (should recompute)
    result3 = obj.cached_prop1
    assert result3 == result1  # Same value
    assert obj.compute_count == 2  # But recomputed


def test_invalidate_cache_partial_clear():
    """Test that invalidate_cache only clears cached properties, not regular attributes."""
    obj = SimpleCacheable(10)

    _ = obj.cached_prop1

    # Invalidate
    obj._invalidate_cache()

    # Regular attributes should remain
    assert obj.value == 10
    assert obj.compute_count == 1


def test_slots_with_dict_works():
    """Test that CacheablePropertiesMixin works with __slots__ that includes __dict__."""
    obj = CacheableWithSlots(10)

    result = obj.cached_prop
    assert result == 20

    # Should be able to use all mixin methods
    assert obj._get_cached_property_status('cached_prop') is True
    obj._invalidate_cache()
    assert obj._get_cached_property_status('cached_prop') is False


def test_slots_without_dict_raises_error():
    """Test that CacheablePropertiesMixin raises TypeError when __dict__ is missing."""
    obj = CacheableWithSlotsNoDict(10)

    # Any method that needs __dict__ should raise TypeError
    with pytest.raises(TypeError, match="does not support cached_property"):
        _ = obj._all_cached_properties_names


def test_ensure_cache_storage_supported_error_message():
    """Test that error message for missing __dict__ is helpful."""
    obj = CacheableWithSlotsNoDict(10)

    with pytest.raises(TypeError) as exc_info:
        _ = obj._all_cached_properties_names

    error_msg = str(exc_info.value)
    assert "lacks __dict__" in error_msg
    assert "__slots__" in error_msg
