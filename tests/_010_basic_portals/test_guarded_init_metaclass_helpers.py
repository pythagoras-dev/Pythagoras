import pytest
from dataclasses import dataclass
from pythagoras._010_basic_portals.guarded_init_metaclass import (
    _validate_pickle_state_integrity,
    _parse_pickle_state,
    _restore_dict_state,
    _restore_slots_state,
    _invoke_post_setstate_hook,
    _re_raise_with_context,
    _raise_if_dataclass,
)

def test_validate_pickle_state_integrity():
    """Test validation of pickle state for forbidden _init_finished=True."""
    # Test valid state (dict)
    _validate_pickle_state_integrity({}, "TestClass")
    _validate_pickle_state_integrity({"_init_finished": False}, "TestClass")
    _validate_pickle_state_integrity(None, "TestClass")

    # Test valid state (tuple)
    _validate_pickle_state_integrity(({}, {}), "TestClass")

    # Test invalid state (dict)
    with pytest.raises(RuntimeError, match="must not be pickled with _init_finished=True"):
        _validate_pickle_state_integrity({"_init_finished": True}, "TestClass")

    # Test invalid state (tuple)
    with pytest.raises(RuntimeError, match="must not be pickled with _init_finished=True"):
         _validate_pickle_state_integrity(({"_init_finished": True}, None), "TestClass")

def test_parse_pickle_state():
    """Test parsing of various pickle state formats."""
    # None
    assert _parse_pickle_state(None, "C") == (None, None)
    
    # Dict
    assert _parse_pickle_state({"a": 1}, "C") == ({"a": 1}, None)
    
    # Tuple (dict, dict)
    assert _parse_pickle_state(({"a": 1}, {"b": 2}), "C") == ({"a": 1}, {"b": 2})
    
    # Tuple (dict, None)
    assert _parse_pickle_state(({"a": 1}, None), "C") == ({"a": 1}, None)
    
    # Tuple (None, dict)
    assert _parse_pickle_state((None, {"b": 2}), "C") == (None, {"b": 2})
    
    # Invalid states
    with pytest.raises(RuntimeError, match="Unsupported pickle state"):
        _parse_pickle_state("invalid", "C")
        
    with pytest.raises(RuntimeError, match="Unsupported pickle state"):
        _parse_pickle_state((1, 2), "C")
        
    with pytest.raises(RuntimeError, match="Unsupported pickle state"):
        _parse_pickle_state((1, 2, 3), "C")

def test_restore_dict_state():
    """Test restoring state into __dict__."""
    class Obj:
        pass
    
    obj = Obj()
    # By default Obj has __dict__
    _restore_dict_state(obj, {"x": 10}, "Obj")
    assert obj.x == 10
    
    class SlotsObj:
        __slots__ = ["x"]
        def __init__(self):
            self.x = 0
    
    slots_obj = SlotsObj()
    with pytest.raises(RuntimeError, match="instance has no __dict__"):
        _restore_dict_state(slots_obj, {"x": 10}, "SlotsObj")

def test_restore_slots_state():
    """Test restoring state into slots."""
    class SlotsObj:
        __slots__ = ["x", "y"]
        def __init__(self):
            self.x = 0
            self.y = 0
        
    obj = SlotsObj()
    _restore_slots_state(obj, {"x": 1, "y": 2})
    assert obj.x == 1
    assert obj.y == 2
    
    # It assumes attributes are valid, if not setattr raises AttributeError usually.
    with pytest.raises(AttributeError):
        _restore_slots_state(obj, {"z": 3})

def test_invoke_post_setstate_hook():
    """Test invocation of __post_setstate__ hook."""
    class Hooked:
        def __init__(self):
            self.called = False
        def __post_setstate__(self):
            self.called = True
            
    obj = Hooked()
    _invoke_post_setstate_hook(obj)
    assert obj.called
    
    class NoHook:
        pass
        
    _invoke_post_setstate_hook(NoHook()) # Should do nothing
    
    class BadHook:
        __post_setstate__ = "not callable"
        
    with pytest.raises(TypeError, match="__post_setstate__ must be callable"):
        _invoke_post_setstate_hook(BadHook())
        
    class FailingHook:
        def __post_setstate__(self):
            raise ValueError("oops")
            
    with pytest.raises(ValueError, match="Error in __post_setstate__: oops"):
        _invoke_post_setstate_hook(FailingHook())

def test_re_raise_with_context():
    """Test exception wrapping logic."""
    # Exception with standard init
    try:
        _re_raise_with_context("MyHook", ValueError("bad value"))
    except ValueError as e:
        assert "Error in MyHook: bad value" in str(e)
        assert isinstance(e, ValueError)
        assert e.__cause__ is not None
        
    # Exception with custom init that might fail with single string
    class CustomError(Exception):
        def __init__(self, arg1, arg2):
            super().__init__(arg1, arg2)
            
    try:
        _re_raise_with_context("MyHook", CustomError("a", "b"))
    except RuntimeError as e:
        assert "Error in MyHook" in str(e)
        assert "CustomError" in str(e)
        assert e.__cause__ is not None
    except CustomError:
        pytest.fail("Should have raised RuntimeError fallback")

def test_raise_if_dataclass():
    """Test detection of dataclasses."""
    @dataclass
    class DC:
        x: int
        
    with pytest.raises(TypeError, match="GuardedInitMeta cannot be used with dataclass"):
        _raise_if_dataclass(DC)
        
    class Normal:
        pass
        
    _raise_if_dataclass(Normal) # Should not raise
