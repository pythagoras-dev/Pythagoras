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
    a = A()
    # Access properties to cache them
    assert a.x == 1
    assert a.y == 2
    assert "x" in a.__dict__
    assert "y" in a.__dict__
    
    a._invalidate_cache()
    
    assert "x" not in a.__dict__
    assert "y" not in a.__dict__
    # Verify they can be recomputed
    assert a.x == 1

def test_cached_properties_names_existence():
    a = A()
    # The property is protected: _all_cached_properties_names
    assert hasattr(a, "_all_cached_properties_names")
    
    names = a._all_cached_properties_names
    assert isinstance(names, (list, set, frozenset))
    assert "x" in names
    assert "y" in names
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
    status = a._get_cached_values_status()
    assert status["x"] is False
    assert status["y"] is False
    
    # Cache x
    _ = a.x
    status = a._get_cached_values_status()
    assert status["x"] is True
    assert status["y"] is False
    
    # Cache y
    _ = a.y
    status = a._get_cached_values_status()
    assert status["x"] is True
    assert status["y"] is True
    
    # Invalidate
    a._invalidate_cache()
    status = a._get_cached_values_status()
    assert status["x"] is False
    assert status["y"] is False

def test_slots_without_dict():
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
    assert s._get_cached_values_status()["val"] is True
    s._invalidate_cache()
    assert "val" not in s.__dict__
