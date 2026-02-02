"""Decorators for building protected functions.

This module provides the protected decorator which wraps callables
into ProtectedFn objects. A ProtectedFn coordinates pre- and post-execution
validation using ValidatorFn instances and executes within a
ProtectedCodePortal context.

The decorator is a thin, declarative layer over the underlying core classes,
allowing you to attach validators at definition
time while keeping function logic clean and focused.
"""

from .protected_portal_core_classes import *
from persidict import Joker, KEEP_CURRENT
from .._110_supporting_utilities import get_long_infoname

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
                 , verbose_logging: bool|Joker|ReuseFlag = KEEP_CURRENT
                 , portal: ProtectedCodePortal | None | ReuseFlag = None
                 ):
        """Initialize the protected decorator.

        Args:
            pre_validators: Pre-execution validators to apply. Each item is
                either a ValidatorFn or a callable that can be wrapped into
                a PreValidatorFn by ProtectedFn.
            post_validators: Post-execution validators to apply. Each item is
                either a ValidatorFn or a callable that can be wrapped into
                a PostValidatorFn by ProtectedFn.
            fixed_kwargs: Keyword arguments to pre-bind to the wrapped function
                for every call.
            verbose_logging: Controls verbose logging behavior. Can be
                True/False to explicitly enable/disable, KEEP_CURRENT to inherit
                from portal/context, or USE_FROM_OTHER to copy from the wrapped
                function (only valid when wrapping an existing ProtectedFn).
            portal: Portal to bind the wrapped function to. Can be a
                ProtectedCodePortal instance, USE_FROM_OTHER to inherit from
                the wrapped function (only valid when wrapping an existing
                ProtectedFn), or None to infer when the function is called.
        """
        if not (isinstance(portal, (ProtectedCodePortal,ReuseFlag)) or portal is None):
            raise TypeError(f"portal must be a ProtectedCodePortal or None, got {get_long_infoname(portal)}")
        autonomous.__init__(self=self
            , portal=portal
            , verbose_logging=verbose_logging
            , fixed_kwargs=fixed_kwargs)
        self._pre_validators = pre_validators
        self._post_validators = post_validators


    def __call__(self, fn: Callable|str) -> ProtectedFn:
        """Wrap the given function into a ProtectedFn.

        Args:
            fn: The target function or its source code string.

        Returns:
            A wrapper that performs pre/post validation and then executes
            the function.
        """
        self._restrict_to_single_thread()
        wrapper = ProtectedFn(fn
                              , portal=self._portal
                              , pre_validators=self._pre_validators
                              , fixed_kwargs=self._fixed_kwargs
                              , post_validators=self._post_validators
                              , verbose_logging=self._verbose_logging)
        return wrapper