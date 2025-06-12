from typing import Callable

from .._020_ordinary_code_portals import ordinary
from .data_portal_core_classes import DataPortal, StorableFn

class storable(ordinary):
    """A decorator that converts a Python function into a StorableFn object.
    """

    def __init__(self
            , portal: DataPortal | None = None):
        assert isinstance(portal, DataPortal) or portal is None
        ordinary.__init__(self=self, portal=portal)

    def __call__(self,fn:Callable)->StorableFn:
        wrapper = StorableFn(fn
            , portal=self._portal)
        return wrapper