"""Foundational portal classes and accessor functions.

This module provides the base classes for Pythagoras portals and utilities
for managing portal lifecycle and access.

Classes:
    BasicPortal: Base class for all portal types. Manages lifecycle and
        registration of portal-aware objects. Not intended for direct use.
    PortalAwareClass: Base class for objects that require portal access.
        May be linked to a specific portal or use the current portal.

Portal Management:
    A Pythagoras application can have multiple portals. Portals become active
    when entered via `with` statement. The current portal (top of the active
    stack) is used by portal-aware objects unless explicitly linked elsewhere.
    If no portal is active when needed, a default portal is auto-created.

Accessor Functions:
    get_current_portal: Get the current active portal.
    get_all_known_portals: List all registered portals.
    get_number_of_known_portals: Count all registered portals.
    get_number_of_active_portals: Count unique portals in the active stack.
    get_default_portal_base_dir: Get the default portal storage location.

Thread Safety:
    Portal operations are NOT thread-safe. All portal access must occur
    from a single thread. Use swarming for multi-process parallelism.
"""

from .basic_portal_core_classes import *
from .basic_portal_accessors import *
from .default_portal_base_dir import get_default_portal_base_dir
from .portal_tester import _PortalTester
# from .portal_tracker import PortalTracker