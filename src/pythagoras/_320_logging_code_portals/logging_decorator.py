"""Decorator for creating logging-enabled functions.

Provides the @logging decorator which wraps ordinary Python functions into
LoggingFn instances that automatically record execution attempts, results,
outputs, crashes, and events via a LoggingCodePortal.
"""

from typing import Callable

from persidict import Joker, KEEP_CURRENT

from .._310_ordinary_code_portals import ordinary, ReuseFlag
from .logging_portal_core_classes import LoggingCodePortal, LoggingFn
from .._110_supporting_utilities import get_long_infoname

class logging(ordinary):
    """Decorator that converts a Python function into a LoggingFn.

    When applied, the target function is wrapped into a LoggingFn that records
    execution attempts, results, outputs, crashes, and events via a
    LoggingCodePortal.
    """
    _excessive_logging: bool|Joker

    def __init__(self
            , excessive_logging:bool|Joker|ReuseFlag = KEEP_CURRENT
            , portal: LoggingCodePortal | ReuseFlag| None = None):
        """Initialize the logging decorator.

        Args:
            excessive_logging: Controls verbose logging behavior. Can be:

                - True/False to explicitly enable/disable detailed per-execution
                  artifacts (attempt context, outputs, and results)
                - KEEP_CURRENT to inherit from the portal
                - USE_FROM_OTHER to copy the setting from the wrapped function
                  (only valid when wrapping an existing LoggingFn)

            portal: Portal to bind the wrapped function to. Can be:

                - A LoggingCodePortal instance to link directly
                - USE_FROM_OTHER to inherit the portal from the wrapped function
                  (only valid when wrapping an existing LoggingFn)
                - None to use the active portal at execution time

        Raises:
            TypeError: If excessive_logging is not a bool, Joker, or ReuseFlag,
                or if portal is not a LoggingCodePortal, ReuseFlag, or None.
        """
        if not isinstance(excessive_logging, (bool, Joker,ReuseFlag)):
            raise TypeError(f"excessive_logging must be bool or Joker or ReuseFlag, got {get_long_infoname(excessive_logging)}")
        if not (isinstance(portal, (LoggingCodePortal,ReuseFlag)) or portal is None):
            raise TypeError(f"portal must be LoggingCodePortal or ReuseFlag or None, got {get_long_infoname(portal)}")
        super().__init__(portal=portal)
        self._excessive_logging = excessive_logging

    def __call__(self,fn:Callable)->LoggingFn:
        """Wrap the function into a LoggingFn.

        Args:
            fn: A plain Python callable to decorate.

        Returns:
            The logging-enabled wrapper for the given function.
        """
        self._restrict_to_single_thread()
        wrapper = LoggingFn(fn
            , excessive_logging=self._excessive_logging
            , portal=self._portal)
        return wrapper