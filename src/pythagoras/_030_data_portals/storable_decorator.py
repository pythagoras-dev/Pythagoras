from typing import Callable

from .._020_ordinary_code_portals import ordinary
from .data_portal_core_classes import DataPortal, StorableFn

class storable(ordinary):
    """Decorator that converts a Python function into a StorableFn.

    When applied, the function is wrapped into a StorableFn that can be
    addressed and stored in a DataPortal.
    """

    def __init__(self
            , portal: DataPortal | None = None):
        """Create a storable decorator bound to an optional DataPortal.

        Args:
            portal: The DataPortal to use as default when wrapping functions.
                If None, the active portal at call time will be used.
        """
        if not (isinstance(portal, DataPortal) or portal is None):
            raise TypeError(f"portal must be a DataPortal or None, "
                            f"got {type(portal).__name__}")
        ordinary.__init__(self=self, portal=portal)

    def __call__(self,fn:Callable)->StorableFn:
        """Wrap the given function into a StorableFn.

        Args:
            fn: The ordinary Python function to wrap.

        Returns:
            StorableFn: A storable function bound to the configured portal.
        """
        wrapper = StorableFn(fn
            , portal=self._portal)
        return wrapper