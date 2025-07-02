from typing import Callable

from .._070_protected_code_portals import protected
from .._060_autonomous_code_portals import AutonomousFn
from .._080_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFn)

from persidict import KEEP_CURRENT, Joker

class pure(protected):

    def __init__(self
                 , pre_validators: list[AutonomousFn] | None = None
                 , post_validators: list[AutonomousFn] | None = None
                 , fixed_kwargs: dict | None = None
                 , excessive_logging: bool | Joker = KEEP_CURRENT
                 , portal: PureCodePortal | None = None
                 ):
        protected.__init__(self=self
                           , portal=portal
                           , excessive_logging=excessive_logging
                           , fixed_kwargs=fixed_kwargs
                           , pre_validators=pre_validators
                           , post_validators=post_validators)


    def __call__(self, fn:Callable|str) -> PureFn:
        wrapper = PureFn(fn
                         , portal=self._portal
                         , pre_validators=self._pre_validators
                         , fixed_kwargs=self._fixed_kwargs
                         , post_validators=self._post_validators
                         , excessive_logging=self._excessive_logging)
        return wrapper

