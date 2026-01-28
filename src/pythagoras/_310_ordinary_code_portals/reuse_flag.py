"""Reuse flag definitions for sharing portal and settings across functions.

This module provides the ReuseFlag singleton class and its USE_FROM_OTHER
instance, which enable copying portal linkage and configuration settings
from one function wrapper to another during construction.
"""

from __future__ import annotations

from typing import Final

from mixinforge import SingletonMixin


class ReuseFlag(SingletonMixin):
    """Singleton flag indicating to reuse settings from another function wrapper.

    When passed as the value for parameters like ``portal`` or ``excessive_logging``
    during function wrapper construction, instructs the constructor to copy that
    setting from the source function (``fn``) if it is an existing wrapper of the
    appropriate type.

    Raises ValueError if the source ``fn`` is not an appropriate wrapper type
    (e.g., using USE_FROM_OTHER for portal when fn is a raw callable).

    See Also:
        USE_FROM_OTHER: The singleton instance of this class to use in code.
    """


USE_FROM_OTHER: Final[ReuseFlag] = ReuseFlag()
"""Singleton flag to inherit settings from an existing function wrapper.

Pass this as the ``portal`` or ``excessive_logging`` argument when constructing
a function wrapper (e.g., OrdinaryFn, LoggingFn) to copy that setting from the
source function. The source function must be an existing wrapper of a compatible
type, otherwise a ValueError is raised.

Example:
    >>> wrapped = LoggingFn(existing_logging_fn, portal=USE_FROM_OTHER)
    >>> # wrapped now uses the same portal as existing_logging_fn
"""