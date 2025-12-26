from __future__ import annotations

from .basic_portal_core_classes import _PORTAL_REGISTRY, BasicPortal, PortalType
from .single_thread_enforcer import _ensure_single_thread


def get_number_of_known_portals(target_portal_type: type[PortalType] = BasicPortal) -> int:
    """Get the number of portals currently in the system.

    Args:
        target_portal_type: Class to filter portals. Default is BasicPortal.
            Only portals that are instances of this class (or subclass)
            are counted.

    Returns:
        The total count of all known portals in the system.
    """
    return _PORTAL_REGISTRY.count_known_portals(target_portal_type)


def get_all_known_portals(target_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
    """Get a list of all known portals.

    Args:
        target_portal_type: Class to filter portals. Default is BasicPortal.
            Only portals that are instances of this class (or subclass)
            are included.

    Returns:
        A list containing all portal instances currently known to the system.
    """
    return _PORTAL_REGISTRY.all_portals(target_portal_type)


def get_number_of_active_portals(target_portal_type: type[PortalType] = BasicPortal) -> int:
    """Get the number of unique portals in the active stack.

    Args:
        target_portal_type: Class to filter portals. Default is BasicPortal.
            Only portals that are instances of this class (or subclass)
            are counted.

    Returns:
        The count of unique portals currently in the active portal stack.
    """
    return _PORTAL_REGISTRY.unique_active_portals_count(target_portal_type)


def get_depth_of_active_portal_stack(target_portal_type: type[PortalType] = BasicPortal) -> int:
    """Get the depth of the active portal stack.

    Args:
        target_portal_type: Class to filter portals. Default is BasicPortal.
            Only portals that are instances of this class (or subclass)
            are included in the depth calculation.

    Returns:
        The total depth (sum of all counters) of the active portal stack.
    """
    return _PORTAL_REGISTRY.active_portals_stack_depth(target_portal_type)


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


def get_nonactive_portals(target_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
    """Get a list of all portals that are not in the active stack.

    Args:
        target_portal_type: Class to filter portals. Default is BasicPortal.
            Only portals that are instances of this class (or subclass)
            are included.

    Returns:
        A list of portal instances that are not currently in the active portal stack.
    """
    return _PORTAL_REGISTRY.nonactive_portals(target_portal_type)


def get_noncurrent_portals(target_portal_type: type[PortalType] = BasicPortal) -> list[PortalType]:
    """Get a list of all portals that are not the current portal.

    Args:
        target_portal_type: Class to filter portals. Default is BasicPortal.
            Only portals that are instances of this class (or subclass)
            are included.

    Returns:
        A list of portal instances that are not currently the active/current portal.
    """
    return _PORTAL_REGISTRY.noncurrent_portals(target_portal_type)
