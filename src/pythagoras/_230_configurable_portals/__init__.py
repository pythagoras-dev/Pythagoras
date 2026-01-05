"""Configuration management layer for Pythagoras portals.

This subpackage provides configuration parameter management for portals and
portal-aware objects. It separates configuration concerns from data storage.

Core Concepts
-------------
**ConfigurablePortal**: Extends DataPortal with persistent configuration storage
and management capabilities. Provides portal-wide and node-specific configuration
settings with caching for efficient access.

**ConfigurableStorableClass**: Base class for portal-aware objects that need
configuration management. Provides methods to get/set configuration settings
in the portal, with support for both portal-wide and object-specific settings.

Exports
-------
- ConfigurablePortal: Portal with configuration management capabilities
- ConfigurableStorableClass: Base class for storable objects with config support
"""

from .configurable_portal_core_classes import (
    ConfigurablePortal, ConfigurableStorableClass)
