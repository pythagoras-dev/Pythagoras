from .._010_basic_portals import BasicPortal
from .swarming_portals import SwarmingPortal

def _set_default_portal():
    """Set the default portal to a SwarmingPortal instance"""
    try:
        if BasicPortal._default_portal is not None:
            return
    except Exception:
        BasicPortal._default_portal = SwarmingPortal()

_set_default_portal()