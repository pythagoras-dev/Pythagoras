"""Decorator for marking functions as pure with automatic result caching.

Pure functions have no side effects and always return the same result for
identical arguments. The @pure() decorator enables persistent caching so that
repeated calls with the same arguments return the cached result without
re-execution.

Pythagoras tracks source code changes in pure functions. When the
implementation changes, the function re-executes on the next call, but
previously cached results remain available for the old version. Only
source code changes for the functon and its pre/post validators are tracked,
not dependencies or environment.
"""

from typing import Callable, Any

from .._350_protected_code_portals import protected, ValidatorFn
from .._360_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFn)

from persidict import KEEP_CURRENT, Joker

class pure(protected):
    """Decorator marking functions as pure with persistent result caching.

    Pure functions are deterministic and side-effect-free. This decorator
    caches execution results persistently, avoids re-execution for identical
    calls, and tracks source code changes to invalidate stale cache entries.

    Extends the protected decorator with pure-function semantics.
    """

    def __init__(self
                 , pre_validators: list[ValidatorFn] | None = None
                 , post_validators: list[ValidatorFn] | None = None
                 , fixed_kwargs: dict[str, Any] | None = None
                 , excessive_logging: bool | Joker = KEEP_CURRENT
                 , portal: PureCodePortal | None = None
                 ):
        """Initialize the pure decorator.

        Args:
            pre_validators: Validators run before execution.
            post_validators: Validators run after execution.
            fixed_kwargs: Argument name-value pairs injected into every call.
            excessive_logging: Enable verbose logging, or KEEP_CURRENT to inherit.
            portal: Specific PureCodePortal to use; inferred from context if omitted.
        """
        protected.__init__(self=self
                           , portal=portal
                           , excessive_logging=excessive_logging
                           , fixed_kwargs=fixed_kwargs
                           , pre_validators=pre_validators
                           , post_validators=post_validators)


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
                         , pre_validators=self._pre_validators
                         , fixed_kwargs=self._fixed_kwargs
                         , post_validators=self._post_validators
                         , excessive_logging=self._excessive_logging)
        return wrapper

