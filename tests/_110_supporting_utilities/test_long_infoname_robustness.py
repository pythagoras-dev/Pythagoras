
import pytest
from pythagoras import get_long_infoname

def test_none_module_in_type():
    # Simulate an object whose type has None as __module__
    TypeWithNoMod = type("TypeWithNoMod", (object,), {})
    TypeWithNoMod.__module__ = None
    
    obj = TypeWithNoMod()
    # New behavior: ignores None module, so just TypeWithNoMod
    res = get_long_infoname(obj)
    assert "TypeWithNoMod" in res
    # Should not start with "None."
    assert not res.startswith("None.")

def test_missing_qualname_in_type():
    # Dynamically created type might miss __qualname__ in older python, but usually has it.
    TypeNoQual = type("TypeNoQual", (object,), {})
    try:
        del TypeNoQual.__qualname__
    except (AttributeError, TypeError):
        pass 
    
    # Just ensure it doesn't crash
    get_long_infoname(TypeNoQual())

def test_object_with_broken_attributes():
    class Broken:
        def __getattribute__(self, item):
            if item in ("__qualname__", "__name__"):
                raise Exception("Don't touch me")
            return object.__getattribute__(self, item)
            
    b = Broken()
    # Should not crash
    try:
        res = get_long_infoname(b)
        # Should contain type info at least (Broken)
        assert "Broken" in res
    except Exception:
        pytest.fail("get_long_infoname crashed on broken attributes")

def test_function_uniqueness():
    def foo(): pass
    
    name = get_long_infoname(foo)
    # Checks for module name
    assert "test_long_infoname_robustness" in name
    # Checks for function type
    assert "function" in name
    # Checks for function name
    assert "foo" in name
    
def test_class_uniqueness():

    class MyClass:
        pass

    name = get_long_infoname(MyClass)
    
    # Checks for module name
    assert "test_long_infoname_robustness" in name
    # Checks for type
    assert "type" in name
    # Checks for class name
    assert "MyClass" in name

def test_none_input():
    assert "builtins.NoneType" == get_long_infoname(None)


def test_partial_uniqueness():
    import functools
    def foo(): pass
    
    p = functools.partial(foo, 10)
    name = get_long_infoname(p)
    
    # Should contain original function's module
    assert "test_long_infoname_robustness" in name
    # Should contain original function name
    assert "foo" in name
    # Should indicate it is a partial
    assert "_partial" in name
    # Should NOT be just "functools.partial"
    assert name != "functools.partial"

def test_basic_types():
    assert "builtins.int" == get_long_infoname(10)
    assert "builtins.str" == get_long_infoname("hello")
