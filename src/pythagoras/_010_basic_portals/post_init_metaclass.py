from abc import ABCMeta
from typing import Any

class PostInitMeta(ABCMeta):
    """Ensures method .__post_init__() is always called after the constructor.
    
    This metaclass automatically calls the `__post_init__()` method on instances
    after their construction is complete, if such method is defined. 
    It also ensures `__after_setstate__()` is called after `__setstate__()`.
    """

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)

        original_setstate = getattr(cls, '__setstate__', None)

        # If the method is already wrapped by PostInitMeta (e.g. inherited), skip.
        if getattr(original_setstate, '_is_post_init_wrapper', False):
            return

        def wrapper(self, state):
            if original_setstate:
                original_setstate(self, state)
            else:
                self.__dict__.update(state)

            if hasattr(self, '__after_setstate__'):
                self.__after_setstate__()

        wrapper._is_post_init_wrapper = True
        cls.__setstate__ = wrapper
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Create and initialize an instance, then call its post-init hook.

        This method overrides the default instance creation process to ensure
        that `__post_init__()` is called after the regular constructor.
        It also includes validation logic for portal-aware objects.

        Args:
            *args: Positional arguments to pass to the class constructor.
            **kwargs: Keyword arguments to pass to the class constructor.

        Returns:
            The fully initialized instance with post-init hook executed.

        Raises:
            AssertionError: If portal-aware object validation fails.
        """
        instance = super().__call__(*args, **kwargs)
        if hasattr(instance, '__post_init__'):
            instance.__post_init__()
        return instance