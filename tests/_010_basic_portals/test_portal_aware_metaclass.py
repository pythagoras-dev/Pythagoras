from pythagoras._010_basic_portals.post_init_metaclass import PostInitMeta

class BasePortalClass(metaclass=PostInitMeta):
    def do_nothing(self):
        pass


class DerivedWithPostInit(metaclass=PostInitMeta):
    def __post_init__(self):
        if not hasattr(self, "post_init_calls"):
            self.post_init_calls = 0
        self.post_init_calls += 1


class DerivedWithCustomSetState(BasePortalClass):
    def __setstate__(self, state):
        self.state = state

    def __after_setstate__(self):
         self.after_setstate_called = True

class SecondDerivedWithCustomSetState(DerivedWithCustomSetState):
    pass

class SecondDerivedWithPostInit(DerivedWithPostInit):
    pass

def test_default_setstate_is_used_for_class_without_setstate():
    """
    Tests that a class with no __setstate__ uses the default logic
    (injected by metaclass) and does not raise errors when setstate is invoked.
    """
    instance = BasePortalClass()

    # Try calling __setstate__:
    # Should not fail, even though it's 'default' logic
    test_state = {"key": "value"}
    # If metaclass adds __setstate__, this should work.
    # If not, and BasePortalClass doesn't have it, it raises AttributeError.
    # The requirement seems to be that PostInitMeta provides this behavior.
    if hasattr(instance, '__setstate__'):
        instance.__setstate__(test_state)
    else:
        # If the original expectation was that it works, then metaclass MUST add it.
        # But standard object doesn't have __setstate__.
        # We will assume checking if it exists is not enough, we want to call it.
        pass
        
    # Wait, the original test called it: instance.__setstate__(test_state)
    # So we expect it to exist.
    instance.__setstate__(test_state)


def test_custom_setstate_is_called_for_class_with_setstate():
    """
    Tests that a class which defines __setstate__ actually calls
    the custom logic, and the new_setstate wraps it properly.
    """
    instance = SecondDerivedWithCustomSetState()

    # Call the setstate method
    test_state = {"foo": "bar"}
    instance.__setstate__(test_state)

    # Verify that the instance now has the 'state' attribute
    # assigned by the custom setstate.
    assert hasattr(instance, "state"), "Custom __setstate__ was not called."
    assert instance.state == test_state, "Custom __setstate__ did not store state correctly."

    # Verify that __after_setstate__ was invoked
    assert hasattr(instance, "after_setstate_called"), "__after_setstate__ was not called."
    assert instance.after_setstate_called is True, "__after_setstate__ was not set to True."


def test_post_init_is_called_if_defined():
    """
    Tests that __post_init__ is invoked after object creation
    if the class defines such a method.
    """
    x = DerivedWithPostInit()
    assert x.post_init_calls == 1, "__post_init__ was not called"

def test_post_init_is_called_in_grand_child():
    """
    Tests that __post_init__ is invoked after object creation
    if the class defines such a method.
    """
    x = SecondDerivedWithPostInit()
    assert x.post_init_calls == 1, "__post_init__ was not called"

def test_after_setstate_is_not_called_if_not_defined():
    """
    Tests that if a class does not define __after_setstate__,
    the code does not fail.
    """
    # Create a class that has its own __setstate__ but no __after_setstate__
    class DerivedNoAfterSetState(BasePortalClass):
        def __setstate__(self, state):
            self.custom_state = state

    instance = DerivedNoAfterSetState()
    # If __after_setstate__ does not exist, it should not be called, nor crash
    instance.__setstate__({"some": "data"})

    assert hasattr(instance, "custom_state"), "Custom __setstate__ was not invoked."
    assert instance.custom_state == {"some": "data"}, "State was not stored."
