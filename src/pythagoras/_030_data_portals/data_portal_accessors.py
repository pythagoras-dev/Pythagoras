from __future__ import annotations

from .. import DataPortal
from .._010_basic_portals.basic_portal_accessors import *


def get_number_of_known_data_portals() -> int:
    """Get the number of DataPortals currently in the system.

    Returns:
        The total count of all known DataPortals in the system.
    """
    return get_number_of_known_portals(DataPortal)


def get_all_known_data_portals() -> list[DataPortal]:
    """Get a list of all known DataPortals.

    Returns:
        A list containing all DataPortal instances currently known to the system.
    """
    return get_all_known_portals(DataPortal)


def get_number_of_active_data_portals() -> int:
    """Get the number of unique DataPortals in the active stack.

    Returns:
        The count of unique DataPortals currently in the active portal stack.
    """
    return get_number_of_active_portals(DataPortal)


def get_depth_of_active_data_portal_stack() -> int:
    """Get the depth of the active DataPortal stack.

    Returns:
        The total depth (sum of all counters) of the active DataPortal stack.
    """
    return get_depth_of_active_portal_stack(DataPortal)


def get_current_data_portal() -> DataPortal:
    """Get the current DataPortal object.

    The current DataPortal is the one that was most recently entered
    using the 'with' statement. If no DataPortal is currently active,
    it finds the most recently created DataPortal and makes it active (and current).
    If there are currently no DataPortals exist in the system,
    it creates the default DataPortal, and makes it active and current.

    Returns:
        The current active DataPortal.
    """
    portal = get_current_portal()
    if not isinstance(portal, DataPortal):
        raise RuntimeError(f"The current portal is {type(portal).__name__}, "
                           f"but a DataPortal was expected.")
    return portal


def get_nonactive_data_portals() -> list[DataPortal]:
    """Get a list of all DataPortals that are not in the active stack.

    Returns:
        A list of DataPortal instances that are not currently in the active portal stack.
    """
    return get_nonactive_portals(DataPortal)


def get_noncurrent_data_portals() -> list[DataPortal]:
    """Get a list of all DataPortals that are not the current portal.

    Returns:
        A list of DataPortal instances that are not currently the active/current portal.
    """
    return get_noncurrent_portals(DataPortal)
