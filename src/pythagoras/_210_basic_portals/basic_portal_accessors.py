"""Accessor functions for retrieving and managing portal objects.

This module provides a public API for accessing portals from the global
portal registry. Functions allow counting portals and retrieving
active/inactive portal lists.
"""

from __future__ import annotations

from .basic_portal_core_classes import _PORTAL_REGISTRY, BasicPortal, PortalType


def get_number_of_known_portals(required_portal_type: type[PortalType] = BasicPortal) -> int:
    """Get the number of portals currently in the system.

    Args:
        required_portal_type: Expected portal type for validation.

    Returns:
        The total count of all known portals in the system.

    Raises:
        TypeError: If any known portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.count_known_portals(required_portal_type)


def get_all_known_portals(required_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
    """Get a list of all known portals.

    Args:
        required_portal_type: Expected portal type for validation.

    Returns:
        All portal instances currently known to the system.

    Raises:
        TypeError: If any known portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.get_all_portals(required_portal_type)


def get_number_of_active_portals(required_portal_type: type[PortalType] = BasicPortal) -> int:
    """Get the number of unique portals in the active stack.

    Args:
        required_portal_type: Expected portal type for validation.

    Returns:
        The count of unique portals currently in the active portal stack.

    Raises:
        TypeError: If any active portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.get_unique_active_portals_count(required_portal_type)


def get_depth_of_active_portal_stack(required_portal_type: type[PortalType] = BasicPortal) -> int:
    """Get the depth of the active portal stack.

    Args:
        required_portal_type: Expected portal type for validation.

    Returns:
        The total depth (sum of all re-entrancy counters) of the active portal stack.

    Raises:
        TypeError: If any active portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.get_active_portals_stack_depth(required_portal_type)


def get_current_portal() -> PortalType:
    """Get the current portal object.

    Returns the most recently entered portal from the active stack. If no portal
    is active, activates the most recently created portal. If no portals exist,
    creates and activates the default portal.

    Returns:
        The current active portal.

    Example:
        >>> portal = get_current_portal()  # Gets or creates default portal
        >>> with CustomPortal() as p:
        ...     assert get_current_portal() is p  # p is now current
    """
    return _PORTAL_REGISTRY.get_current_portal()


def get_nonactive_portals(required_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
    """Get a list of all portals that are not in the active stack.

    Args:
        required_portal_type: Expected portal type for validation.

    Returns:
        Portal instances that are not currently in the active portal stack.

    Raises:
        TypeError: If any non-active portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.get_nonactive_portals(required_portal_type)


def get_noncurrent_portals(required_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
    """Get a list of all portals that are not the current portal.

    Args:
        required_portal_type: Expected portal type for validation.

    Returns:
        Portal instances that are not currently the active/current portal.

    Raises:
        TypeError: If any non-current portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.get_noncurrent_portals(required_portal_type)
