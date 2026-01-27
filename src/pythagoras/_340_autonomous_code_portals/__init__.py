"""Autonomous code execution infrastructure for Pythagoras.

This subpackage extends SafeCodePortal with self-contained execution support
and autonomous primitives. Autonomous functions are self-contained: they can
only use built-ins and names imported inside their own body.

Core Concepts
-------------
**AutonomousCodePortal**: Extends SafeCodePortal with self-contained execution
support and autonomous primitives.

**AutonomousFn**: Function wrapper created by the @autonomous decorator.
Extends SafeFn with autonomy enforcement. Only regular (non-async) functions
are supported; methods, closures, and lambdas cannot be autonomous.

**AutonomousFnCallSignature**: Unique identifier combining an AutonomousFn
and its arguments, used to organize and retrieve execution artifacts.

Exports
-------
Portal and function classes:
- AutonomousCodePortal: Portal with autonomous execution support
- AutonomousFn: Wrapper for self-contained functions
- AutonomousFnCallSignature: Identifier for a specific AutonomousFn call

Decorator:
- autonomous: Convert functions to AutonomousFn instances
"""

from .autonomous_portal_core_classes import *
from .autonomous_decorators import *

