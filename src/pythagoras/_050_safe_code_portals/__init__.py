"""Classes and functions that allow safe execution of code.

The main classes in this sub-package are SafeCodePortal and SafeFn,
which extend LoggingCodePortal and LoggingFn
to provide safe execution capabilities for logging functions.

SafeFn functions can't access (hence can't harm) any data/devices outside
the function's local scope and the portal.

This functionality has not been implemented yet.
It will be done soon by integrating https://pypi.org/project/RestrictedPython/
"""

from .safe_portal_core_classes import *
from .safe_decorator import *