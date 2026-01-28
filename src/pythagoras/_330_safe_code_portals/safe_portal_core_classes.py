"""Classes and functions that allow safe execution of code.

The main classes in this sub-package are SafeCodePortal and SafeFn,
which extend LoggingCodePortal and LoggingFn
to provide safe execution capabilities for logging functions.

SafeFn functions can't access (hence can't harm) any data/devices outside
the function's local scope and the portal.

This functionality has not been implemented yet.
It will be done soon by integrating https://pypi.org/project/RestrictedPython/
"""

from __future__ import annotations

from .._320_logging_code_portals.logging_portal_core_classes import *
from .._110_supporting_utilities import get_long_infoname


class SafeCodePortal(LoggingCodePortal):
    """A portal that executes functions with logging under a "safe" contract.

    Currently, SafeCodePortal inherits all behavior from LoggingCodePortal.
    True sandboxing/isolation has not yet been implemented and will be
    introduced in the future (see Notes).

    Notes:
        The actual safety guarantees (prohibiting access to external
        filesystem, network, process state, etc.) are not yet enforced.
        The plan is to integrate RestrictedPython to implement a proper
        sandbox. Until then, SafeCodePortal behaves like LoggingCodePortal
        but keeps the API intended for safe execution.
    """

    def __init__(self
                 , root_dict: PersiDict|str|None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 ):
        """Initialize a SafeCodePortal.

        Args:
            root_dict: Root persistent dictionary or its path used by the
                underlying data portal for storing execution artifacts. If a
                string is provided, it is treated as a path on disk. If None,
                an in-memory structure may be used (depending on configuration).
            excessive_logging: Whether to enable verbose logging of execution
                attempts, results, outputs and events. Use KEEP_CURRENT to
                inherit the active setting from parent context.
        """
        LoggingCodePortal.__init__(self
            , root_dict=root_dict
            , excessive_logging=excessive_logging)


class SafeFnCallSignature(LoggingFnCallSignature):
    """A signature object describing a call to a SafeFn.

    This specialization only narrows the types returned by some accessors
    (e.g., fn) to Safe* counterparts. All logging behavior and storage layout
    are inherited from LoggingFnCallSignature.
    """

    def __init__(self, fn: SafeFn, arguments: dict):
        """Construct a signature for a specific SafeFn call.

        Args:
            fn: The safe function object to be called.
            arguments: The keyword arguments to use for the call.

        Raises:
            TypeError: If fn is not a SafeFn instance or arguments is not a dict.
        """
        if not isinstance(fn, SafeFn):
            raise TypeError(f"fn must be a SafeFn instance, got {get_long_infoname(fn)}")
        if not isinstance(arguments, dict):
            raise TypeError(f"arguments must be a dict, got {get_long_infoname(arguments)}")
        super().__init__(fn, arguments)

    @cached_property
    def fn(self) -> SafeFn:
        """Return the SafeFn referenced by this signature.

        Returns:
            The underlying safe function instance.
        """
        return super().fn


class SafeFn(LoggingFn):
    """A function wrapper intended for safe execution within a portal.

    SafeFn currently behaves like LoggingFn, adding only type-narrowed
    accessors for convenience. Future versions will enforce sandboxed
    execution (see Notes).

    Notes:
        No actual sandboxing is performed yet. Behavior equals LoggingFn.
    """

    def __init__(self
                 , fn: Callable|str
                 , portal: LoggingCodePortal|None|ReuseFlag = None
                 , excessive_logging: bool|Joker|ReuseFlag = KEEP_CURRENT
                 ):
        """Create a SafeFn wrapper.

        Args:
            fn: The Python callable to wrap or its source code string.
            portal: Portal to associate with this function. Can be:

                - A SafeCodePortal instance to link directly
                - USE_FROM_OTHER to inherit the portal from ``fn`` when ``fn``
                  is an existing SafeFn
                - None to use the active portal at execution time

            excessive_logging: Controls verbose logging behavior. Can be:

                - True/False to explicitly enable/disable
                - KEEP_CURRENT to inherit from the surrounding context
                - USE_FROM_OTHER to copy the setting from ``fn`` when ``fn``
                  is an existing SafeFn
        """
        LoggingFn.__init__(self
            , fn = fn
            , portal=portal
            , excessive_logging=excessive_logging)


    def __getstate__(self):
        """Return picklable state.

        Returns:
            The state returned by the parent LoggingFn for pickling.
        """
        state = super().__getstate__()
        return state


    def __setstate__(self, state):
        """Restore object state after unpickling.

        Args:
            state: The state previously produced by __getstate__.
        """
        super().__setstate__(state)


    @property
    def portal(self) -> SafeCodePortal:
        """Return the associated SafeCodePortal.

        Returns:
            The portal that owns this function.
        """
        return super().portal


    def get_signature(self, arguments:dict) -> SafeFnCallSignature:
        """Create a SafeFnCallSignature for a given call.

        Args:
            arguments: The keyword arguments for the call.

        Returns:
            A typed call signature suitable for execution and logging
            through the portal.
        """
        return SafeFnCallSignature(fn=self, arguments=arguments)