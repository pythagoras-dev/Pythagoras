"""The @ordinary decorator for converting functions to OrdinaryFn objects.

This module provides the ordinary class, a decorator that transforms regular
Python functions into Pythagoras OrdinaryFn objects while enforcing ordinarity
constraints (keyword-only arguments, no defaults, etc.).
"""

from typing import Callable, Any

from mixinforge import SingleThreadEnforcerMixin

from .ordinary_portal_core_classes import OrdinaryFn, OrdinaryCodePortal
from .reuse_flag import ReuseFlag
from .._110_supporting_utilities import get_long_infoname


class ordinary(SingleThreadEnforcerMixin):
    """A decorator that converts a Python function into an OrdinaryFn object.

    Transforms regular Python functions into Pythagoras OrdinaryFn wrappers,
    enabling them to participate in the Pythagoras execution model. The
    decorator validates ordinarity constraints (no closures, no defaults,
    keyword-args only) and prepares the function for normalized execution.

    The decorator instance maintains optional portal linkage that will be
    transferred to all functions it wraps. This allows entire modules or
    function groups to be associated with specific portals.

    Note:
        Decorator instances are stateless beyond portal linkage and should
        not be pickled. Functions wrapped by this decorator become OrdinaryFn
        instances, which ARE picklable (without portal references).
    """

    _portal: OrdinaryCodePortal | None

    def __init__(self, portal: OrdinaryCodePortal | ReuseFlag | None = None):
        """Initialize the decorator with optional portal linkage.

        Args:
            portal: Optional portal to associate with wrapped functions.
        """
        super().__init__()
        self._restrict_to_single_thread()
        if not (portal is None or isinstance(portal, (OrdinaryCodePortal, ReuseFlag))):
            raise TypeError(f"portal must be an OrdinaryCodePortal, ReuseFlag, or None, got {get_long_infoname(portal)}")
        self._portal = portal

    def __call__(self, fn: Callable) -> OrdinaryFn:
        """Wrap a function and return its OrdinaryFn representation.

        Args:
            fn: The function to wrap.

        Returns:
            OrdinaryFn wrapper for the provided function.
        """
        self._restrict_to_single_thread()
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
            state: The state object to restore.

        Raises:
            TypeError: Always, as decorators should not be pickled.
        """
        raise TypeError("Decorators cannot be pickled.")