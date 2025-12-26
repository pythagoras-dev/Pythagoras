from functools import cached_property
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
    if not hasattr(a, "all_cached_properties_names"):
        pytest.fail("all_cached_properties_names property missing")
    
    names = a.all_cached_properties_names
    # Checking what we expect. Assuming list[str] or set[str] based on "names"
    # If the user strictly demanded 'str', we might need to adjust.
    # But usually 'names' implies collection.
    assert isinstance(names, (list, set))
    assert "x" in names
    assert "y" in names
    assert "z" not in names
