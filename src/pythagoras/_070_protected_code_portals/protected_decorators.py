"""Support for work with protected functions."""

from typing import Callable

from src.pythagoras._060_autonomous_code_portals import autonomous, AutonomousFn
from .protected_portal_core_classes import ProtectedFn, ProtectedCodePortal

class protected(autonomous):

    _guards: list[AutonomousFn] | None
    _validators: list[AutonomousFn] | None

    def __init__(self
                 , guards: list[AutonomousFn] | None = None
                 , validators: list[AutonomousFn] | None = None
                 , fixed_kwargs: dict | None = None
                 , excessive_logging: bool|None = None
                 , portal: ProtectedCodePortal | None = None
                 ):
        assert isinstance(portal, ProtectedCodePortal) or portal is None
        assert isinstance(fixed_kwargs, dict) or fixed_kwargs is None
        autonomous.__init__(self=self
            , portal=portal
            , excessive_logging=excessive_logging
            , fixed_kwargs=fixed_kwargs)
        self._guards = guards
        self._validators = validators


    def __call__(self, fn: Callable|str) -> ProtectedFn:
        wrapper = ProtectedFn(fn
            ,portal=self._portal
            ,guards=self._guards
            ,fixed_kwargs=self._fixed_kwargs
            ,validators=self._validators
            ,excessive_logging=self._excessive_logging)
        return wrapper