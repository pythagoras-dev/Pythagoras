"""Support for work with protected functions."""

from typing import Callable, Any

from .validator_fn_classes import ValidatorFn
from .._060_autonomous_code_portals import autonomous
from .protected_portal_core_classes import ProtectedFn, ProtectedCodePortal
from persidict import Joker, KEEP_CURRENT

class protected(autonomous):

    _pre_validators: list[ValidatorFn] | None
    _post_validators: list[ValidatorFn] | None

    def __init__(self
                 , pre_validators: list[ValidatorFn] | None = None
                 , post_validators: list[ValidatorFn] | None = None
                 , fixed_kwargs: dict[str,Any] | None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 , portal: ProtectedCodePortal | None = None
                 ):
        assert isinstance(portal, ProtectedCodePortal) or portal is None
        assert isinstance(fixed_kwargs, dict) or fixed_kwargs is None
        autonomous.__init__(self=self
            , portal=portal
            , excessive_logging=excessive_logging
            , fixed_kwargs=fixed_kwargs)
        self._pre_validators = pre_validators
        self._post_validators = post_validators


    def __call__(self, fn: Callable|str) -> ProtectedFn:
        wrapper = ProtectedFn(fn
                              , portal=self._portal
                              , pre_validators=self._pre_validators
                              , fixed_kwargs=self._fixed_kwargs
                              , post_validators=self._post_validators
                              , excessive_logging=self._excessive_logging)
        return wrapper