"""Decorator to work with pure functions.

A pure function is a protected function that has no side effects and
always returns the same result if it is called multiple times
with the same arguments.

This subpackage defines a decorator which is used to inform Pythagoras that
a function is intended to be pure: @pure().

Pythagoras persistently caches results, produced by a pure function, so that
if the function is called multiple times with the same arguments,
the function is executed only once, and the cached result is returned
for all the subsequent executions.

While caching the results of a pure function, Pythagoras also tracks
changes in the source code of the function. If the source code of a pure
function changes, the function is executed again on the next call.
However, the previously cached results are still available
for the old version of the function. Only changes in the function's
source code are tracked.
"""

from typing import Callable, Any

from .._070_protected_code_portals import protected, ValidatorFn
from .._080_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFn)

from persidict import KEEP_CURRENT, Joker

class pure(protected):
    """Decorator that marks a function as pure and enables result caching.

    Pure functions are assumed to be deterministic and free of side effects:
    given the same arguments they always produce the same result. When you
    decorate a function with @pure(), Pythagoras caches execution results in
    a persistent store, avoids re-executing the function for identical calls,
    as well as tracks source-code changes to recompute the function
    when necessary.

    This decorator is a thin, typed wrapper over the generic `protected`
    decorator configured for pure-function semantics.
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
            pre_validators: Optional list of validator functions that run
                before execution.
            post_validators: Optional list of validator functions that run
                after execution to validate results or side conditions.
            fixed_kwargs: Mapping of argument names to values that will be
                always injected into the decorated function calls.
            excessive_logging: Controls verbosity inside the portal; keep
                KEEP_CURRENT to inherit from the active portal, True/False to
                override.
            portal: Optional PureCodePortal to bind the decorated function to.
                If omitted, the portal(s) to use will be inferred
                during the function call(s).
        """
        protected.__init__(self=self
                           , portal=portal
                           , excessive_logging=excessive_logging
                           , fixed_kwargs=fixed_kwargs
                           , pre_validators=pre_validators
                           , post_validators=post_validators)


    def __call__(self, fn:Callable|str) -> PureFn:
        """Wrap a function as a PureFn within a PureCodePortal.

        Args:
            fn: The target callable or its import path string.

        Returns:
            PureFn: A wrapped function instance that supports memoized
            execution via run/swarm/execute and address-based retrieval.
        """
        wrapper = PureFn(fn
                         , portal=self._portal
                         , pre_validators=self._pre_validators
                         , fixed_kwargs=self._fixed_kwargs
                         , post_validators=self._post_validators
                         , excessive_logging=self._excessive_logging)
        return wrapper

