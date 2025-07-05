from typing import Callable

from persidict import Joker, KEEP_CURRENT

from .._040_logging_code_portals import logging
from .safe_portal_core_classes import SafeFn, SafeCodePortal


class safe(logging):
    """A decorator that converts a Python function into a SafeFn object.
    """

    def __init__(self
                 , excessive_logging: bool|None|Joker = KEEP_CURRENT
                 , portal: SafeCodePortal | None = None):
        assert isinstance(portal, SafeCodePortal) or portal is None
        logging.__init__(self=self
            , portal=portal
            , excessive_logging=excessive_logging)


    def __call__(self,fn:Callable)->SafeFn:
        wrapper = SafeFn(fn
            , portal=self._portal
            , excessive_logging=self._excessive_logging)
        return wrapper