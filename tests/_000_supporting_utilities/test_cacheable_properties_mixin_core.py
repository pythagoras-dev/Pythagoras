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

def test_cached_properties_names_existence():
    a = A()
    # The property is protected: _all_cached_properties_names
    assert hasattr(a, "_all_cached_properties_names")

    names = a._all_cached_properties_names
    # Contract: must return frozenset specifically
    assert isinstance(names, frozenset)
    assert "x" in names
    assert "y" in names
    # Regular @property should not be included
    assert "z" not in names

def test_invalidate_cache():
    """Test that _invalidate_cache() removes all cached values from __dict__."""
    a = A()
    # Access properties to cache them
    assert a.x == 1
    assert a.y == 2
    assert a.z == 3  # regular property
    assert "x" in a.__dict__
    assert "y" in a.__dict__
    assert "z" not in a.__dict__  # regular property doesn't cache

    a._invalidate_cache()

    assert "x" not in a.__dict__
    assert "y" not in a.__dict__
    # Verify they can be recomputed
    assert a.x == 1
    # Regular property still works
    assert a.z == 3

def test_invalidate_cache_idempotency():
    """Test that calling _invalidate_cache() multiple times is safe."""
    a = A()

    # Cache some properties
    _ = a.x
    _ = a.y
    assert "x" in a.__dict__
    assert "y" in a.__dict__

    # First invalidation
    a._invalidate_cache()
    assert "x" not in a.__dict__
    assert "y" not in a.__dict__

    # Second invalidation should be safe (no error)
    a._invalidate_cache()
    assert "x" not in a.__dict__
    assert "y" not in a.__dict__

    # Third invalidation should also be safe
    a._invalidate_cache()

    # Properties should still be recomputable
    assert a.x == 1
    assert a.y == 2

def test_status_reporting():
    a = A()
    # Initially nothing cached
    status = a._get_all_cached_properties_status()
    assert status["x"] is False
    assert status["y"] is False

    # Cache x
    _ = a.x
    status = a._get_all_cached_properties_status()
    assert status["x"] is True
    assert status["y"] is False

    # Cache y
    _ = a.y
    status = a._get_all_cached_properties_status()
    assert status["x"] is True
    assert status["y"] is True

    # Invalidate
    a._invalidate_cache()
    status = a._get_all_cached_properties_status()
    assert status["x"] is False
    assert status["y"] is False

def test_empty_class():
    """Test that classes with no cached properties work correctly."""
    class Empty(CacheablePropertiesMixin):
        def regular_method(self):
            return 1

    e = Empty()
    names = e._all_cached_properties_names
    assert isinstance(names, frozenset)
    assert len(names) == 0

    # Should not raise, even with no cached properties
    e._invalidate_cache()

    status = e._get_all_cached_properties_status()
    assert isinstance(status, dict)
    assert len(status) == 0

def test_property_that_raises():
    """Test that cached properties raising exceptions don't break cache management."""
    class RaisingProp(CacheablePropertiesMixin):
        @cached_property
        def failing_prop(self):
            raise ValueError("computation failed")

        @cached_property
        def working_prop(self):
            return 42

    r = RaisingProp()

    # Discover properties even if they raise
    assert "failing_prop" in r._all_cached_properties_names
    assert "working_prop" in r._all_cached_properties_names

    # Access working property
    assert r.working_prop == 42
    assert "working_prop" in r.__dict__

    # failing_prop should raise
    with pytest.raises(ValueError, match="computation failed"):
        _ = r.failing_prop

    # failing_prop should not be cached (cached_property only caches on success)
    assert "failing_prop" not in r.__dict__

    # Invalidate should work regardless
    r._invalidate_cache()
    assert "working_prop" not in r.__dict__

def test_inheritance():
    class Base(CacheablePropertiesMixin):
        @cached_property
        def base_prop(self):
            return "base"

    class Child(Base):
        @cached_property
        def child_prop(self):
            return "child"

    c = Child()
    names = c._all_cached_properties_names
    assert "base_prop" in names
    assert "child_prop" in names

    # Access to cache
    assert c.base_prop == "base"
    assert c.child_prop == "child"
    assert "base_prop" in c.__dict__
    assert "child_prop" in c.__dict__

    c._invalidate_cache()
    assert "base_prop" not in c.__dict__
    assert "child_prop" not in c.__dict__

def test_multiple_inheritance_diamond():
    """Test that cached properties are discovered correctly in diamond inheritance."""
    class Base(CacheablePropertiesMixin):
        @cached_property
        def base_prop(self):
            return "base"

    class Left(Base):
        @cached_property
        def left_prop(self):
            return "left"

    class Right(Base):
        @cached_property
        def right_prop(self):
            return "right"

    class Diamond(Left, Right):
        @cached_property
        def diamond_prop(self):
            return "diamond"

    d = Diamond()
    names = d._all_cached_properties_names

    # All properties should be discovered exactly once
    assert "base_prop" in names
    assert "left_prop" in names
    assert "right_prop" in names
    assert "diamond_prop" in names

    # Access all properties
    assert d.base_prop == "base"
    assert d.left_prop == "left"
    assert d.right_prop == "right"
    assert d.diamond_prop == "diamond"

    # All should be cached
    assert all(name in d.__dict__ for name in names)

    # Invalidate should clear all
    d._invalidate_cache()
    assert all(name not in d.__dict__ for name in names)

def test_slots_without_dict():
    """Test that classes with __slots__ but no __dict__ raise clear errors."""
    class SlotsOnly(CacheablePropertiesMixin):
        __slots__ = ("_val",)

        @cached_property
        def val(self):
            return 1

    s = SlotsOnly()
    # Should raise TypeError because __dict__ is missing
    with pytest.raises(TypeError, match="lacks __dict__"):
        _ = s._all_cached_properties_names

    with pytest.raises(TypeError, match="lacks __dict__"):
        s._invalidate_cache()

def test_slots_with_dict():
    class SlotsWithDict(CacheablePropertiesMixin):
        __slots__ = ("__dict__",)

        @cached_property
        def val(self):
            return 42

    s = SlotsWithDict()
    assert s.val == 42
    assert "val" in s._all_cached_properties_names
    assert s._get_all_cached_properties_status()["val"] is True
    s._invalidate_cache()
    assert "val" not in s.__dict__
