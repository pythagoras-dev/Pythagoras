from .._090_swarming_portals import SwarmingPortal
from .._010_basic_portals import get_default_portal_base_dir


def instantiate_default_local_portal():
    SwarmingPortal(root_dict = get_default_portal_base_dir())