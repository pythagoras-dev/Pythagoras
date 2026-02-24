"""Decorator for marking functions as pure with automatic result caching.

Pure functions have no side effects and always return the same result for
identical arguments. The @pure() decorator enables persistent caching so that
repeated calls with the same arguments return the cached result without
re-execution.

Pythagoras tracks source code changes in pure functions. When the
implementation changes, the function re-executes on the next call, but
previously cached results remain available for the old version. Only
source code changes for the function and its requirements/result checks
are tracked, not dependencies or environment.
"""

from typing import Callable, Any

from .._310_ordinary_code_portals import ReuseFlag
from .._350_guarded_code_portals import guarded, ExtensionFn
from .._360_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFn)

from persidict import KEEP_CURRENT, Joker

class pure(guarded):
    """Decorator marking functions as pure with persistent result caching.

    Pure functions are deterministic and side-effect-free. This decorator
    caches execution results persistently, avoids re-execution for identical
    calls, and tracks source code changes to invalidate stale cache entries.

    Extends the guarded decorator with pure-function semantics.
    """

    def __init__(self
                 , requirements: list[ExtensionFn] | None = None
                 , result_checks: list[ExtensionFn] | None = None
                 , fixed_kwargs: dict[str, Any] | None = None
                 , verbose_logging: bool | Joker | ReuseFlag = KEEP_CURRENT
                 , portal: PureCodePortal | None | ReuseFlag = None
                 ):
        """Initialize the pure decorator.

        Args:
            requirements: Requirements run before execution.
            result_checks: Result checks run after execution.
            fixed_kwargs: Argument name-value pairs injected into every call.
            verbose_logging: Controls verbose logging behavior. Can be:

                - True/False to explicitly enable/disable
                - KEEP_CURRENT to inherit from context
                - USE_FROM_OTHER to copy the setting from the wrapped function
                  (only valid when wrapping an existing PureFn)

            portal: Portal to use for caching and execution. Can be:

                - A PureCodePortal instance to link directly
                - USE_FROM_OTHER to inherit the portal from the wrapped function
                  (only valid when wrapping an existing PureFn)
                - None to infer from context at execution time
        """
        super().__init__(portal=portal
                       , verbose_logging=verbose_logging
                       , fixed_kwargs=fixed_kwargs
                       , requirements=requirements
                       , result_checks=result_checks)


    def __call__(self, fn:Callable|str) -> PureFn:
        """Wrap a function as a PureFn with caching semantics.

        Args:
            fn: Target callable.

        Returns:
            Wrapped function supporting cached execution and address-based retrieval.
        """
        self._restrict_to_single_thread()
        wrapper = PureFn(fn
                         , portal=self._portal
                         , requirements=self._requirements
                         , fixed_kwargs=self._fixed_kwargs
                         , result_checks=self._result_checks
                         , verbose_logging=self._verbose_logging)
        return wrapper
