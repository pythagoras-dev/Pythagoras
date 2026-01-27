"""Foundational portal classes and accessor functions.

This module provides the base classes for Pythagoras portals and utilities
for managing portal lifecycle and access.

BasicPortal is the base class for all portal types. It manages lifecycle and
registration of portal-aware objects. Not intended for direct use.

PortalAwareObject is the base class for objects that require portal access.
Instances may be linked to a specific portal or use the current portal.

A Pythagoras application can have multiple portals. Portals become active
when entered via `with` statement. The current portal (top of the active
stack) is used by default by portal-aware objects unless explicitly linked
elsewhere.

Portal operations are NOT thread-safe. All portal access must occur from a
single thread.
"""

from .basic_portal_core_classes import *
from .basic_portal_accessors import *
from .default_portal_base_dir import *
from .portal_tester import _PortalTester as _PortalTester