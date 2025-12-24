
import pytest
import pickle
from dataclasses import dataclass
from pythagoras._010_basic_portals.guarded_init_metaclass import GuardedInitMeta

# --- Helper classes for pickling tests (must be at module level) ---

class PickleClass(metaclass=GuardedInitMeta):
    def __init__(self, value):
        self._init_finished = False
        self.value = value

    def __getstate__(self):
        state = self.__dict__.copy()
        if "_init_finished" in state:
            del state["_init_finished"]
        return state

class BadPickleClass(metaclass=GuardedInitMeta):
    def __init__(self):
        self._init_finished = False

class PostSetStateClass(metaclass=GuardedInitMeta):
    def __init__(self):
        self._init_finished = False
        self.restored = False

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('_init_finished', None)
        return state

    def __post_setstate__(self):
        self.restored = True

class ErrorPostSetStateClass(metaclass=GuardedInitMeta):
    def __init__(self):
        self._init_finished = False

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('_init_finished', None)
        return state

    def __post_setstate__(self):
        raise ValueError("Restoration failed")

# --- Tests ---

def test_basic_initialization():
    """Test that initialization works correctly when contract is followed."""
    class GoodClass(metaclass=GuardedInitMeta):
        def __init__(self):
            self._init_finished = False
            self.value = 10

    obj = GoodClass()
    assert obj._init_finished is True
    assert obj.value == 10

def test_missing_init_flag():
    """Test that RuntimeError is raised if _init_finished is not set to False in __init__."""
    class BadClass(metaclass=GuardedInitMeta):
        def __init__(self):
            self.value = 10
            # Missing self._init_finished = False

    with pytest.raises(RuntimeError, match="must set attribute _init_finished to False"):
        BadClass()

def test_post_init_hook():
    """Test that __post_init__ is called."""
    class PostInitClass(metaclass=GuardedInitMeta):
        def __init__(self):
            self._init_finished = False
            self.initialized_count = 0
            
        def __post_init__(self):
            self.initialized_count += 1

    obj = PostInitClass()
    assert obj._init_finished is True
    assert obj.initialized_count == 1

def test_post_init_error():
    """Test that errors in __post_init__ are re-raised with context."""
    class ErrorPostInitClass(metaclass=GuardedInitMeta):
        def __init__(self):
            self._init_finished = False
            
        def __post_init__(self):
            raise ValueError("Something went wrong")

    with pytest.raises(ValueError, match="Error in __post_init__"):
        ErrorPostInitClass()

def test_dataclass_rejection():
    """Test that applying GuardedInitMeta to a dataclass raises TypeError on instantiation."""
    # Note: definition succeeds because is_dataclass is false during __init__
    @dataclass
    class MyDataclass(metaclass=GuardedInitMeta):
        x: int

    with pytest.raises(TypeError, match="GuardedInitMeta cannot be used with dataclass"):
        MyDataclass(10)

def test_pickle_success():
    """Test successful pickle/unpickle cycle with proper __getstate__."""
    obj = PickleClass(42)
    assert obj._init_finished is True
    
    data = pickle.dumps(obj)
    new_obj = pickle.loads(data)
    
    assert new_obj.value == 42
    assert new_obj._init_finished is True
    assert isinstance(new_obj, PickleClass)

def test_pickle_failure_if_init_finished_present():
    """Test that unpickling fails if _init_finished=True is present in state."""
    obj = BadPickleClass()
    # Default pickling includes _init_finished=True
    data = pickle.dumps(obj)
    
    with pytest.raises(RuntimeError, match="must not be pickled with _init_finished=True"):
        pickle.loads(data)

def test_post_setstate_hook():
    """Test that __post_setstate__ is called after unpickling."""
    obj = PostSetStateClass()
    data = pickle.dumps(obj)
    new_obj = pickle.loads(data)
    
    assert new_obj.restored is True
    assert new_obj._init_finished is True

def test_post_setstate_error():
    """Test that errors in __post_setstate__ are re-raised with context."""
    obj = ErrorPostSetStateClass()
    data = pickle.dumps(obj)
    
    with pytest.raises(ValueError, match="Error in __post_setstate__"):
        pickle.loads(data)
