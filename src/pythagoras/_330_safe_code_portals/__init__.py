"""Safe execution infrastructure for Pythagoras (not yet implemented).

This subpackage extends LoggingCodePortal with sandboxed execution capabilities,
restricting functions from accessing external resources outside their local
scope and the portal.

Core Concepts
-------------
**SafeCodePortal**: Extends LoggingCodePortal with sandboxed execution.
SafeFn functions registered with this portal will be prevented from accessing
external filesystem, network, process state, etc. Currently behaves like
LoggingCodePortal; sandboxing will be implemented via RestrictedPython.

**SafeFn**: Function wrapper created by the @safe decorator. Extends LoggingFn
with execution isolation. Currently behaves like LoggingFn until sandboxing
is implemented.

**SafeFnCallSignature**: Unique identifier combining a SafeFn and its arguments,
used to organize and retrieve execution artifacts in storage.

Exports
-------
Portal and function classes:
- SafeCodePortal: Portal with sandboxed execution (not yet enforced)
- SafeFn: Wrapper for functions with execution isolation
- SafeFnCallSignature: Identifier for a specific SafeFn call

Decorator:
- safe: Convert functions to SafeFn instances

Note:
    Sandboxing is not yet implemented. Integration with RestrictedPython
    (https://pypi.org/project/RestrictedPython/) is planned.
"""

from .safe_portal_core_classes import *
from .safe_decorator import *