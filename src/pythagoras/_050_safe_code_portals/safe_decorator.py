from typing import Callable

from persidict import Joker, KEEP_CURRENT

from .._040_logging_code_portals import logging
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
                 , excessive_logging: bool|None|Joker = KEEP_CURRENT
                 , portal: SafeCodePortal | None = None):
        """Create a safe decorator bound to an optional portal.

        Args:
            excessive_logging: Whether to enable verbose logging for wrapped
                calls. KEEP_CURRENT inherits from current context.
            portal: The SafeCodePortal to attach the resulting SafeFn to. If
                None, the active portal (if any) may be used by lower layers.
        """
        if not (isinstance(portal, SafeCodePortal) or portal is None):
            raise TypeError(f"portal must be a SafeCodePortal or None, got {type(portal).__name__}")
        logging.__init__(self=self
            , portal=portal
            , excessive_logging=excessive_logging)


    def __call__(self,fn:Callable)->SafeFn:
        """Wrap a Python callable into a SafeFn.

        Args:
            fn: The function to wrap.

        Returns:
            SafeFn: The wrapped function that can be executed via a portal and
            will record logging information.
        """
        wrapper = SafeFn(fn
            , portal=self._portal
            , excessive_logging=self._excessive_logging)
        return wrapper