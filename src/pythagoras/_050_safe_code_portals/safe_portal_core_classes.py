from __future__ import annotations

from typing import Callable

from parameterizable import register_parameterizable_class
from persidict import PersiDict, Joker, KEEP_CURRENT

from .._040_logging_code_portals.logging_portal_core_classes import (
    LoggingCodePortal, LoggingFn)


class SafeCodePortal(LoggingCodePortal):
    def __init__(self
                 , root_dict: PersiDict|str|None = None
                 , p_consistency_checks: float|Joker = KEEP_CURRENT
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 ):
        LoggingCodePortal.__init__(self
            , root_dict=root_dict
            , p_consistency_checks=p_consistency_checks
            , excessive_logging=excessive_logging)


class SafeFn(LoggingFn):
    def __init__(self
                 , fn: Callable|str
                 , portal: LoggingCodePortal|None = None
                 , excessive_logging: bool|Joker = KEEP_CURRENT
                 ):
        LoggingFn.__init__(self
            , fn = fn
            , portal=portal
            , excessive_logging=excessive_logging)
        if isinstance(fn, SafeFn):
            return

    def __getstate__(self):
        state = super().__getstate__()
        return state


    def __setstate__(self, state):
        self._invalidate_cache()
        super().__setstate__(state)


    @property
    def portal(self) -> SafeCodePortal:
        return LoggingFn.portal.__get__(self)


    @portal.setter
    def portal(self, new_portal: SafeCodePortal) -> None:
        if not isinstance(new_portal, SafeCodePortal):
            raise TypeError("portal must be a LoggingCodePortal instance")
        LoggingFn.portal.__set__(self, new_portal)


register_parameterizable_class(SafeCodePortal)