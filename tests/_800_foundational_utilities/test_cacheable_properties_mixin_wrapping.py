from functools import cached_property
from pythagoras._800_foundational_utilities.cacheable_properties_mixin import CacheablePropertiesMixin

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

    class Wrapped(CacheablePropertiesMixin):
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

    class DeepWrapped(CacheablePropertiesMixin):
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
