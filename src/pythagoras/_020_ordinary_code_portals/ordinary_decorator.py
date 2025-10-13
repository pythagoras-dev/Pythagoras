from typing import Callable

from .ordinary_portal_core_classes import OrdinaryFn, OrdinaryCodePortal


class ordinary:
    """A decorator that converts a Python function into an OrdinaryFn object.

    As a part of the conversion process, the source code of the function
    is checked. If it does not meet the requirements of an ordinary function,
    an exception is raised.
    """

    _portal: OrdinaryCodePortal | None

    def __init__(self, portal: OrdinaryCodePortal | None = None):
       """Initialize the decorator.

       Args:
           portal: Optional OrdinaryCodePortal to link to the resulting
               OrdinaryFn wrappers.
       """
       if not (portal is None or isinstance(portal, OrdinaryCodePortal)):
           raise TypeError(f"portal must be an OrdinaryCodePortal or None, got {type(portal).__name__}")
       self._portal=portal


    def __call__(self,fn:Callable)->OrdinaryFn:
        """Wrap a callable and return its OrdinaryFn representation.

        Args:
            fn: The function to convert into an OrdinaryFn.

        Returns:
            OrdinaryFn: The wrapper around the provided function.
        """
        wrapper = OrdinaryFn(fn, portal=self._portal)
        return wrapper


    def __getstate__(self):
        """This method is called when the object is pickled."""
        raise TypeError("Decorators cannot be pickled.")


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        raise TypeError("Decorators cannot be pickled.")