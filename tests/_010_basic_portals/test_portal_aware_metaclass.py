#
# class BasePortalClass(metaclass=PortalAwareMetaclass):
#     def do_nothing(self):
#         pass
#
#
# class DerivedWithAfterInit(metaclass=PortalAwareMetaclass):
#     def __after_init__(self):
#         if not hasattr(self, "after_init_calls"):
#             self.after_init_calls = 0
#         self.after_init_calls += 1
#
#
# class DerivedWithCustomSetState(BasePortalClass):
#     def __setstate__(self, state):
#         self.state = state
#
#     def __after_setstate__(self):
#          self.after_setstate_called = True
#
# class SecondDerivedWithCustomSetState(DerivedWithCustomSetState):
#     pass
#
# class SecondDerivedWithAfterInit(DerivedWithAfterInit):
#     pass
#
# def test_default_setstate_is_used_for_class_without_setstate():
#     """
#     Tests that a class with no __setstate__ uses the default logic
#     and does not raise errors when setstate is invoked.
#     """
#     instance = BasePortalClass()
#
#     # Try calling __setstate__:
#     # Should not fail, even though it's 'default' logic
#     test_state = {"key": "value"}
#     instance.__setstate__(test_state)
#
#
# def test_custom_setstate_is_called_for_class_with_setstate():
#     """
#     Tests that a class which defines __setstate__ actually calls
#     the custom logic, and the new_setstate wraps it properly.
#     """
#     instance = SecondDerivedWithCustomSetState()
#
#     # Call the setstate method
#     test_state = {"foo": "bar"}
#     instance.__setstate__(test_state)
#
#     # Verify that the instance now has the 'state' attribute
#     # assigned by the custom setstate.
#     assert hasattr(instance, "state"), "Custom __setstate__ was not called."
#     assert instance.state == test_state, "Custom __setstate__ did not store state correctly."
#
#     # Verify that __after_setstate__ was invoked
#     assert hasattr(instance, "after_setstate_called"), "__after_setstate__ was not called."
#     assert instance.after_setstate_called is True, "__after_setstate__ was not set to True."
#
#
# def test_after_init_is_called_if_defined():
#     """
#     Tests that __after_init__ is invoked after object creation
#     if the class defines such a method.
#     """
#     x = DerivedWithAfterInit()
#     assert x.after_init_calls == 1, "__after_init__ was not called"
#
# def test_after_init_is_called_in_grand_child():
#     """
#     Tests that __after_init__ is invoked after object creation
#     if the class defines such a method.
#     """
#     x = SecondDerivedWithAfterInit()
#     assert x.after_init_calls == 1, "__after_init__ was not called"
#
# def test_after_setstate_is_not_called_if_not_defined():
#     """
#     Tests that if a class does not define __after_setstate__,
#     the code does not fail.
#     """
#     # Create a class that has its own __setstate__ but no __after_setstate__
#     class DerivedNoAfterSetState(BasePortalClass):
#         def __setstate__(self, state):
#             self.custom_state = state
#
#     instance = DerivedNoAfterSetState()
#     # If __after_setstate__ does not exist, it should not be called, nor crash
#     instance.__setstate__({"some": "data"})
#
#     assert hasattr(instance, "custom_state"), "Custom __setstate__ was not invoked."
#     assert instance.custom_state == {"some": "data"}, "State was not stored."
#
#
