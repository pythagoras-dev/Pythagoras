"""Classes and functions that allow safe execution of code.

The main classes in this sub-package are SafeCodePortal and SafeFn,
which extend LoggingCodePortal and LoggingFn
to provide safe execution capabilities for logging functions.

SafeFn functions can't access (hence can't harm) any data/devices outside
the function's local scope and the portal.

This functionality has not been implemented yet.
It will be done soon by integrating https://pypi.org/project/RestrictedPython/
"""

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


    def __getstate__(self):
        """This method is called when the object is pickled."""
        state = super().__getstate__()
        return state


    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        super().__setstate__(state)


    @property
    def portal(self) -> SafeCodePortal:
        return super().portal


register_parameterizable_class(SafeCodePortal)