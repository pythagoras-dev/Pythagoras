"""Decorator for creating safe-execution-enabled functions.

Provides the @safe decorator which wraps ordinary Python functions into
SafeFn instances that execute within a SafeCodePortal context with logging
and (planned) sandboxing capabilities.
"""
from typing import Callable

from persidict import Joker, KEEP_CURRENT

from .. import ReuseFlag
from .._320_logging_code_portals import logging
from .._110_supporting_utilities import get_long_infoname
from .safe_portal_core_classes import SafeFn, SafeCodePortal


class safe(logging):
    """Decorator that wraps a callable into a SafeFn for portal execution.

    Usage:
        @safe()
        def my_fn(x: int) -> int:
            return x + 1

    Notes:
        This decorator configures only logging-related behavior for now. Actual
        safety/sandboxing is not yet implemented.
    """

    def __init__(self
                 , excessive_logging: bool|None|Joker|ReuseFlag = KEEP_CURRENT
                 , portal: SafeCodePortal | None|ReuseFlag = None):
        """Create a safe decorator bound to an optional portal.

        Args:
            excessive_logging: Controls verbose logging behavior. Can be:

                - True/False to explicitly enable/disable
                - KEEP_CURRENT to inherit from current context
                - USE_FROM_OTHER to copy the setting from the wrapped function
                  (only valid when wrapping an existing SafeFn)

            portal: Portal to attach the resulting SafeFn to. Can be:

                - A SafeCodePortal instance to link directly
                - USE_FROM_OTHER to inherit the portal from the wrapped function
                  (only valid when wrapping an existing SafeFn)
                - None to use the active portal at execution time

        Raises:
            TypeError: If portal is not a SafeCodePortal, ReuseFlag, or None.
        """
        if not (isinstance(portal, (SafeCodePortal,ReuseFlag)) or portal is None):
            raise TypeError(f"portal must be a SafeCodePortal or ReuseFlag or None, got {get_long_infoname(portal)}")
        logging.__init__(self=self
            , portal=portal
            , excessive_logging=excessive_logging)


    def __call__(self,fn:Callable)->SafeFn:
        """Wrap a Python callable into a SafeFn.

        Args:
            fn: The function to wrap.

        Returns:
            The wrapped function that can be executed via a portal and
            will record logging information.
        """
        self._restrict_to_single_thread()
        wrapper = SafeFn(fn
            , portal=self._portal
            , excessive_logging=self._excessive_logging)
        return wrapper