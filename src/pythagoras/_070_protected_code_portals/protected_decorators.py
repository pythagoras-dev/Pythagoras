"""Decorators for building protected functions.

This module provides the protected decorator which wraps callables
into ProtectedFn objects. A ProtectedFn coordinates pre- and post-execution
validation using ValidatorFn instances and executes within a
ProtectedCodePortal context.

The decorator is a thin, declarative layer over the underlying core classes,
allowing you to attach validators at definition
time while keeping function logic clean and focused.
"""

from typing import Callable, Any

# from .validator_fn_classes import ValidatorFn
from .._060_autonomous_code_portals import autonomous
from .protected_portal_core_classes import *
from persidict import Joker, KEEP_CURRENT

class protected(autonomous):
    """Decorator for protected functions with pre/post validation.

    This decorator wraps a target callable into a ProtectedFn that enforces
    a sequence of pre- and post-execution validators. It builds on the
    autonomous decorator, adding validator support to it.

    Typical usage:
        @protected(pre_validators=[...], post_validators=[...])
        def fn(...):
            ...

    See Also:
        ProtectedFn: The runtime wrapper that performs validation and execution.
        ProtectedCodePortal: Portal coordinating protected function execution.

    Attributes:
        _pre_validators (list[ValidatorFn] | None): Validators executed before
            the target function.
        _post_validators (list[ValidatorFn] | None): Validators executed after
            the target function.
    """

    _pre_validators: list[ValidatorFn] | None
    _post_validators: list[ValidatorFn] | None

    def __init__(self
                 , pre_validators: list[ValidatorFn] | None = None
                 , post_validators: list[ValidatorFn] | None = None
                 , fixed_kwargs: dict[str,Any] | None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , portal: ProtectedCodePortal | None = None
                 ):
        """Initialize the protected decorator.

        Args:
            pre_validators (list[ValidatorFn] | None): Pre-execution validators
                to apply. Each item is either a ValidatorFn or a callable that
                can be wrapped into a PreValidatorFn by ProtectedFn.
            post_validators (list[ValidatorFn] | None): Post-execution validators
                to apply. Each item is either a ValidatorFn or a callable that
                can be wrapped into a PostValidatorFn by ProtectedFn.
            fixed_kwargs (dict[str, Any] | None): Keyword arguments to pre-bind
                to the wrapped function for every call.
            excessive_logging (bool | Joker): Enables verbose logging for the
                wrapped function and its validators. Use KEEP_CURRENT to inherit
                the current setting from the portal/context.
            portal (ProtectedCodePortal | None): Optional portal instance to
                bind the wrapped function to. If None, a suitable portal will be
                inferred when fuction is called.
        """
        if not (isinstance(portal, ProtectedCodePortal) or portal is None):
            raise TypeError(f"portal must be a ProtectedCodePortal or None, got {type(portal).__name__}")
        if not (isinstance(fixed_kwargs, dict) or fixed_kwargs is None):
            raise TypeError(f"fixed_kwargs must be a dict or None, got {type(fixed_kwargs).__name__}")
        autonomous.__init__(self=self
            , portal=portal
            , excessive_logging=excessive_logging
            , fixed_kwargs=fixed_kwargs)
        self._pre_validators = pre_validators
        self._post_validators = post_validators


    def __call__(self, fn: Callable|str) -> ProtectedFn:
        """Wrap the given function into a ProtectedFn.

        Args:
            fn (Callable | str): The target function or its source code string.

        Returns:
            ProtectedFn: A wrapper that performs pre/post validation and then
            executes the function.
        """
        wrapper = ProtectedFn(fn
                              , portal=self._portal
                              , pre_validators=self._pre_validators
                              , fixed_kwargs=self._fixed_kwargs
                              , post_validators=self._post_validators
                              , excessive_logging=self._excessive_logging)
        return wrapper