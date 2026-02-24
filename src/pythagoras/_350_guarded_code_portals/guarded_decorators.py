"""Decorators for building guarded functions.

This module provides the guarded decorator which wraps callables
into GuardedFn objects. A GuardedFn coordinates pre- and post-execution
checks using ExtensionFn instances and executes within a
GuardedCodePortal context.

The decorator is a thin, declarative layer over the underlying core classes,
allowing you to attach requirements and result checks at definition
time while keeping function logic clean and focused.
"""

from .guarded_portal_core_classes import *
from persidict import Joker, KEEP_CURRENT
from .._110_supporting_utilities import get_long_infoname

class guarded(autonomous):
    """Decorator for guarded functions with requirements/result checks.

    This decorator wraps a target callable into a GuardedFn that enforces
    a sequence of pre- and post-execution checks. It builds on the
    autonomous decorator, adding extension support to it.

    Typical usage:
        @guarded(requirements=[...], result_checks=[...])
        def fn(...):
            ...

    See Also:
        GuardedFn: The runtime wrapper that performs checks and execution.
        GuardedCodePortal: Portal coordinating guarded function execution.

    Attributes:
        _requirements (list[ExtensionFn] | None): Requirements executed before
            the target function.
        _result_checks (list[ExtensionFn] | None): Result checks executed after
            the target function.
    """

    _requirements: list[ExtensionFn] | None
    _result_checks: list[ExtensionFn] | None

    def __init__(self
                 , requirements: list[ExtensionFn] | None = None
                 , result_checks: list[ExtensionFn] | None = None
                 , fixed_kwargs: dict[str,Any] | None = None
                 , verbose_logging: bool|Joker|ReuseFlag = KEEP_CURRENT
                 , portal: GuardedCodePortal | None | ReuseFlag = None
                 ):
        """Initialize the guarded decorator.

        Args:
            requirements: Pre-execution requirements to apply. Each item is
                either an ExtensionFn or a callable that can be wrapped into
                a RequirementFn by GuardedFn.
            result_checks: Post-execution result checks to apply. Each item is
                either an ExtensionFn or a callable that can be wrapped into
                a ResultCheckFn by GuardedFn.
            fixed_kwargs: Keyword arguments to pre-bind to the wrapped function
                for every call.
            verbose_logging: Controls verbose logging behavior. Can be
                True/False to explicitly enable/disable, KEEP_CURRENT to inherit
                from portal/context, or USE_FROM_OTHER to copy from the wrapped
                function (only valid when wrapping an existing GuardedFn).
            portal: Portal to bind the wrapped function to. Can be a
                GuardedCodePortal instance, USE_FROM_OTHER to inherit from
                the wrapped function (only valid when wrapping an existing
                GuardedFn), or None to infer when the function is called.
        """
        if not (isinstance(portal, (GuardedCodePortal,ReuseFlag)) or portal is None):
            raise TypeError(f"portal must be a GuardedCodePortal or None, got {get_long_infoname(portal)}")
        autonomous.__init__(self=self
            , portal=portal
            , verbose_logging=verbose_logging
            , fixed_kwargs=fixed_kwargs)
        self._requirements = requirements
        self._result_checks = result_checks


    def __call__(self, fn: Callable|str) -> GuardedFn:
        """Wrap the given function into a GuardedFn.

        Args:
            fn: The target function or its source code string.

        Returns:
            A wrapper that performs requirement/result checks and then executes
            the function.
        """
        self._restrict_to_single_thread()
        wrapper = GuardedFn(fn
                              , portal=self._portal
                              , requirements=self._requirements
                              , fixed_kwargs=self._fixed_kwargs
                              , result_checks=self._result_checks
                              , verbose_logging=self._verbose_logging)
        return wrapper
