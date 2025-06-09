from typing import Callable

from .._070_protected_code_portals import protected
from .._060_autonomous_code_portals import AutonomousFn
from .._080_pure_code_portals.pure_core_classes import (
    PureCodePortal, PureFn)



class pure(protected):

    def __init__(self
                 , guards: list[AutonomousFn] | None = None
                 , validators: list[AutonomousFn] | None = None
                 , fixed_kwargs: dict | None = None
                 , excessive_logging: bool | None = None
                 , portal: PureCodePortal | None = None
                 ):
        protected.__init__(self=self
            , portal=portal
            , excessive_logging=excessive_logging
            , fixed_kwargs=fixed_kwargs
            , guards=guards
            , validators=validators)


    def __call__(self, fn:Callable|str) -> PureFn:
        wrapper = PureFn(fn
            , portal=self._portal
            , guards=self._guards
            , fixed_kwargs=self._fixed_kwargs
            , validators=self._validators
            , excessive_logging=self._excessive_logging)
        return wrapper

