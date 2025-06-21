from typing import Callable

from persidict import Joker, KEEP_CURRENT

from .._030_data_portals import storable
from .logging_portal_core_classes import LoggingCodePortal, LoggingFn

class logging(storable):
    """A decorator that converts a Python function into a LoggingFn object.
    """
    _excessive_logging: bool|Joker

    def __init__(self
            , excessive_logging:bool|Joker = KEEP_CURRENT
            , portal: LoggingCodePortal | None = None):
        assert isinstance(excessive_logging, (bool,Joker))
        assert isinstance(portal, LoggingCodePortal) or portal is None
        storable.__init__(self=self, portal=portal)
        self._excessive_logging = excessive_logging

    def __call__(self,fn:Callable)->LoggingFn:
        wrapper = LoggingFn(fn
            , excessive_logging=self._excessive_logging
            , portal=self._portal)
        return wrapper