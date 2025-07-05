from .._010_basic_portals import get_active_portal
from .._010_basic_portals import get_default_portal_base_dir
from .._090_swarming_portals import SwarmingPortal


def _instantiate_default_local_portal():
    #NB: there is a hidden circular dependency from get_active_portal()
    SwarmingPortal(root_dict = get_default_portal_base_dir())