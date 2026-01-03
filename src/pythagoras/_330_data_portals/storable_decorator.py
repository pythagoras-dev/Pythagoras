"""The @storable decorator for converting functions to StorableFn objects.

This module provides the storable decorator, which extends the @ordinary
decorator to create functions that can be stored in and retrieved from
DataPortals using content-addressable storage.

Storable functions are automatically assigned a ValueAddr based on their
normalized source code, enabling:
- Persistent storage across application runs
- Sharing functions between distributed processes via DataPortals
- Content-based deduplication (identical functions share storage)
- Per-portal configuration for function behavior
"""
from typing import Callable

from .._210_basic_portals import ensure_single_thread
from .._320_ordinary_code_portals import ordinary
from .data_portal_core_classes import DataPortal, StorableFn

class storable(ordinary):
    """Decorator that converts a Python function into a StorableFn.

    Extends the @ordinary decorator to create functions with content-addressable
    storage capabilities. Wrapped functions are automatically assigned a ValueAddr
    and can be stored in/retrieved from DataPortals.

    Like @ordinary, this decorator validates ordinarity constraints (no closures,
    no defaults, keyword-only args). Beyond that, it enables persistent storage
    and cross-process function sharing through the portal system.

    The decorator instance can be linked to a specific DataPortal, which will be
    used by all functions it wraps. Otherwise, functions use the current active
    portal.

    Example:
        >>> @storable
        ... def compute(x, y):
        ...     return x + y
        >>> compute.addr  # ValueAddr for the function
        >>> compute(x=1, y=2)  # Stored in current portal
        3
    """

    def __init__(self
            , portal: DataPortal | None = None):
        """Create a storable decorator bound to an optional DataPortal.

        Args:
            portal: Optional DataPortal to link wrapped functions to. If provided,
                all functions wrapped by this decorator instance will be associated
                with this portal. If None, wrapped functions use the current active
                portal at runtime.

        Raises:
            TypeError: If portal is not a DataPortal or None.
        """
        if not (isinstance(portal, DataPortal) or portal is None):
            raise TypeError(f"portal must be a DataPortal or None, "
                            f"got {type(portal).__name__}")
        ordinary.__init__(self=self, portal=portal)

    def __call__(self,fn:Callable)->StorableFn:
        """Wrap a function into a StorableFn with content-addressable storage.

        Validates ordinarity constraints and creates a StorableFn wrapper that
        automatically computes the function's ValueAddr and enables portal storage.

        Args:
            fn: The Python function to wrap. Must satisfy ordinarity constraints
                (no closures, no defaults, keyword-only arguments).

        Returns:
            StorableFn wrapper around the provided function, linked to the
            decorator's portal (if any).

        Raises:
            FunctionError: If fn violates ordinarity constraints.
        """
        ensure_single_thread()
        wrapper = StorableFn(fn
            , portal=self._portal)
        return wrapper