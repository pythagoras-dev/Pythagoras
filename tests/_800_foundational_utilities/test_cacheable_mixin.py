from functools import cached_property, wraps
from pythagoras._800_foundational_utilities.cacheable_mixin import CacheableMixin
import pytest

class A(CacheableMixin):
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

def test_inheritance():
    class Base(CacheableMixin):
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

def test_wrapped_descriptor():
    """Test that cached_property discovery works through __wrapped__ chains."""
    # Simulate a decorator that wraps the descriptor
    def descriptor_wrapper(descriptor):
        class Wrapper:
            def __init__(self, wrapped):
                self.__wrapped__ = wrapped
            def __set_name__(self, owner, name):
                if hasattr(self.__wrapped__, "__set_name__"):
                    self.__wrapped__.__set_name__(owner, name)
            def __get__(self, instance, owner):
                return self.__wrapped__.__get__(instance, owner)
        return Wrapper(descriptor)

    class Wrapped(CacheableMixin):
        @descriptor_wrapper
        @cached_property
        def wrapped_prop(self):
            return "wrapped"

    w = Wrapped()
    # Check discovery
    assert "wrapped_prop" in w._all_cached_properties_names

    # Check functionality (invalidation relies on name only, so it should work
    # as long as the property puts the value in __dict__ under the same name)
    # Note: cached_property stores value in __dict__[name].
    # Our wrapper delegates __get__, so cached_property.__get__ executes.
    # cached_property.__get__ writes to __dict__['wrapped_prop'].

    assert w.wrapped_prop == "wrapped"
    assert "wrapped_prop" in w.__dict__

    w._invalidate_cache()
    assert "wrapped_prop" not in w.__dict__
    assert w.wrapped_prop == "wrapped"

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

def test_slots_without_dict():
    """Test that classes with __slots__ but no __dict__ raise clear errors."""
    class SlotsOnly(CacheableMixin):
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
    class SlotsWithDict(CacheableMixin):
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

def test_empty_class():
    """Test that classes with no cached properties work correctly."""
    class Empty(CacheableMixin):
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
    class RaisingProp(CacheableMixin):
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

def test_multiple_inheritance_diamond():
    """Test that cached properties are discovered correctly in diamond inheritance."""
    class Base(CacheableMixin):
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

def test_deep_wrapping_chain():
    """Test that __wrapped__ unwrapping respects the depth limit."""
    # Create a wrapper that creates a chain of given depth
    def create_deep_wrapper(wrapped_obj, depth):
        """Create a chain of wrappers with __wrapped__ attributes."""
        current = wrapped_obj
        for _ in range(depth):
            class Wrapper:
                def __init__(self, inner):
                    self.__wrapped__ = inner
                def __get__(self, instance, owner):
                    if hasattr(self.__wrapped__, '__get__'):
                        return self.__wrapped__.__get__(instance, owner)
                    return self.__wrapped__
            current = Wrapper(current)
        return current

    class DeepWrapped(CacheableMixin):
        pass

    # Manually add wrapped properties to the class
    prop_shallow = cached_property(lambda self: "shallow")
    prop_shallow.__set_name__(DeepWrapped, "shallow_wrapped")
    DeepWrapped.shallow_wrapped = create_deep_wrapper(prop_shallow, 50)

    prop_deep = cached_property(lambda self: "deep")
    prop_deep.__set_name__(DeepWrapped, "deep_wrapped")
    DeepWrapped.deep_wrapped = create_deep_wrapper(prop_deep, 150)

    d = DeepWrapped()
    names = d._all_cached_properties_names

    # shallow_wrapped should be discovered (within depth limit of 100)
    assert "shallow_wrapped" in names

    # deep_wrapped should NOT be discovered (exceeds depth limit of 100)
    assert "deep_wrapped" not in names

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
    class Base(CacheableMixin):
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
    class Counter(CacheableMixin):
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
