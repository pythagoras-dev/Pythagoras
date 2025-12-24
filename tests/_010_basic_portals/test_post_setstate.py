
import pickle
from pythagoras._010_basic_portals.guarded_init_metaclass import GuardedInitMeta

class MyClass(metaclass=GuardedInitMeta):
    def __init__(self, value):
        self._init_finished = False
        self.value = value
        self.post_setstate_called = False
        
    def __post_setstate__(self):
        self.post_setstate_called = True

    def __getstate__(self):
        state = self.__dict__.copy()
        if "_init_finished" in state:
            del state["_init_finished"]
        return state

class TestPostSetState:
    def test_post_setstate_called(self):
        obj = MyClass(10)
        assert not obj.post_setstate_called # Should be False initially

        # Pickle
        dumped = pickle.dumps(obj)
        
        # Unpickle
        loaded = pickle.loads(dumped)
        
        # Check if post_setstate was called
        assert loaded.post_setstate_called
        assert loaded.value == 10
        assert loaded._init_finished
