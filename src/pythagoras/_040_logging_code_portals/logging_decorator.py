from typing import Callable

from persidict import Joker, KEEP_CURRENT

from .._030_data_portals import storable
from .logging_portal_core_classes import LoggingCodePortal, LoggingFn

class logging(storable):
    """Decorator that converts a Python function into a LoggingFn.

    When applied, the target function is wrapped into a LoggingFn that records
    execution attempts, results, outputs, crashes, and events via a
    LoggingCodePortal.
    """
    _excessive_logging: bool|Joker

    def __init__(self
            , excessive_logging:bool|Joker = KEEP_CURRENT
            , portal: LoggingCodePortal | None = None):
        """Initialize the logging decorator.

        Args:
            excessive_logging: If True, the wrapped function will capture
                detailed per-execution artifacts (attempt context, outputs,
                and results). If KEEP_CURRENT, inherits from the wrapped
                LoggingFn or the active portal.
            portal: Optional LoggingCodePortal to bind the wrapped function to.
                If None, the active portal at execution time is used.
        """
        if not isinstance(excessive_logging, (bool, Joker)):
            raise TypeError(f"excessive_logging must be bool or Joker, got {type(excessive_logging).__name__}")
        if not (isinstance(portal, LoggingCodePortal) or portal is None):
            raise TypeError(f"portal must be LoggingCodePortal or None, got {type(portal).__name__}")
        storable.__init__(self=self, portal=portal)
        self._excessive_logging = excessive_logging

    def __call__(self,fn:Callable)->LoggingFn:
        """Wrap the function into a LoggingFn.

        Args:
            fn: A plain Python callable to decorate.

        Returns:
            LoggingFn: The logging-enabled wrapper for the given function.
        """
        wrapper = LoggingFn(fn
            , excessive_logging=self._excessive_logging
            , portal=self._portal)
        return wrapper