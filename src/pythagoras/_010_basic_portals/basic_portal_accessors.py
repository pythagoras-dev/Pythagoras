"""Accessor functions for retrieving and managing portal objects.

This module provides a public API for accessing portals from the global
portal registry. Functions allow querying by fingerprint, counting portals,
and retrieving active/inactive portal lists.
"""

from __future__ import annotations

from .basic_portal_core_classes import _PORTAL_REGISTRY, BasicPortal, PortalType, PortalStrFingerprint


def get_portal_by_fingerprint(
        portal_fingerprint: PortalStrFingerprint,
        required_portal_type: type[PortalType] = BasicPortal
        ) -> PortalType:
    """Get a portal by its fingerprint.

    Args:
        portal_fingerprint: The unique string fingerprint identifying the portal.
        required_portal_type: Class to validate the portal against. Default is BasicPortal.
            If the found portal is not an instance of this class (or subclass),
            a TypeError is raised.

    Returns:
        The portal instance matching the fingerprint.

    Raises:
        TypeError: If the found portal is not an instance of required_portal_type,
            or if portal_fingerprint is not a string.
        KeyError: If no portal with the given fingerprint exists.
    """
    return _PORTAL_REGISTRY.get_portal_by_fingerprint(
        portal_fingerprint,required_portal_type)


def get_number_of_known_portals(required_portal_type: type[PortalType] = BasicPortal) -> int:
    """Get the number of portals currently in the system.

    Args:
        required_portal_type: Class to validate portals. Default is BasicPortal.
            If any known portal is not an instance of this class (or subclass),
            a TypeError is raised.

    Returns:
        The total count of all known portals in the system.

    Raises:
        TypeError: If any known portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.count_known_portals(required_portal_type)


def get_all_known_portals(required_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
    """Get a list of all known portals.

    Args:
        required_portal_type: Class to validate portals. Default is BasicPortal.
            If any known portal is not an instance of this class (or subclass),
            a TypeError is raised.

    Returns:
        A list containing all portal instances currently known to the system.

    Raises:
        TypeError: If any known portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.all_portals(required_portal_type)


def get_all_known_portal_fingerprints(
        required_portal_type: type[PortalType] = BasicPortal
        ) -> set[PortalStrFingerprint]:
    """Get a set of all known portal fingerprints.

    Args:
        required_portal_type: Class to validate portals. Default is BasicPortal.
            If any known portal is not an instance of this class (or subclass),
            a TypeError is raised.

    Returns:
        A set containing fingerprints of all portals currently known to the system.

    Raises:
        TypeError: If any known portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.all_portal_fingerprints(required_portal_type)


def get_number_of_active_portals(required_portal_type: type[PortalType] = BasicPortal) -> int:
    """Get the number of unique portals in the active stack.

    Args:
        required_portal_type: Class to validate portals. Default is BasicPortal.
            If any active portal is not an instance of this class (or subclass),
            a TypeError is raised.

    Returns:
        The count of unique portals currently in the active portal stack.

    Raises:
        TypeError: If any active portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.unique_active_portals_count(required_portal_type)


def get_depth_of_active_portal_stack(required_portal_type: type[PortalType] = BasicPortal) -> int:
    """Get the depth of the active portal stack.

    Args:
        required_portal_type: Class to validate portals. Default is BasicPortal.
            If any active portal is not an instance of this class (or subclass),
            a TypeError is raised.

    Returns:
        The total depth (sum of all counters) of the active portal stack.

    Raises:
        TypeError: If any active portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.active_portals_stack_depth(required_portal_type)


def get_current_portal() -> PortalType:
    """Get the current portal object.

    The current portal is the one that was most recently entered
    using the 'with' statement. If no portal is currently active,
    it finds the most recently created portal and makes it active (and current).
    If there are currently no portals exist in the system,
    it creates the default portal, and makes it active and current.

    Returns:
        The current active portal.
    """
    return _PORTAL_REGISTRY.current_portal()


def get_nonactive_portals(required_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
    """Get a list of all portals that are not in the active stack.

    Args:
        required_portal_type: Class to validate portals. Default is BasicPortal.
            If any non-active portal is not an instance of this class (or subclass),
            a TypeError is raised.

    Returns:
        A list of portal instances that are not currently in the active portal stack.

    Raises:
        TypeError: If any non-active portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.nonactive_portals(required_portal_type)


def get_noncurrent_portals(required_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
    """Get a list of all portals that are not the current portal.

    Args:
        required_portal_type: Class to validate portals. Default is BasicPortal.
            If any non-current portal is not an instance of this class (or subclass),
            a TypeError is raised.

    Returns:
        A list of portal instances that are not currently the active/current portal.

    Raises:
        TypeError: If any non-current portal is not an instance of required_portal_type.
    """
    return _PORTAL_REGISTRY.noncurrent_portals(required_portal_type)
