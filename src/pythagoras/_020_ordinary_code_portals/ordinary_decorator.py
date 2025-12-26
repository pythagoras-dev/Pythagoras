"""The @ordinary decorator for converting functions to OrdinaryFn objects.

This module provides the `ordinary` class, which serves as a decorator to
transform regular Python functions into Pythagoras OrdinaryFn objects,
enforcing "ordinarity" constraints (no *args, no defaults, etc.).
"""

from typing import Callable, Any

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
        self._portal = portal

    def __call__(self, fn: Callable) -> OrdinaryFn:
        """Wrap a callable and return its OrdinaryFn representation.

        Args:
            fn: The function to convert into an OrdinaryFn.

        Returns:
            The wrapper around the provided function.
        """
        wrapper = OrdinaryFn(fn, portal=self._portal)
        return wrapper

    def __getstate__(self) -> Any:
        """Prevent pickling of the decorator instance.

        Raises:
            TypeError: Always, as decorators are not meant to be pickled.
        """
        raise TypeError("Decorators cannot be pickled.")

    def __setstate__(self, state: Any) -> None:
        """Prevent unpickling of the decorator instance.

        Args:
            state: The state object to restore (unused).

        Raises:
            TypeError: Always, as decorators are not meant to be pickled.
        """
        raise TypeError("Decorators cannot be pickled.")