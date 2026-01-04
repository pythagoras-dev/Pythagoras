from .._210_basic_portals import get_default_portal_base_dir
from .._210_basic_portals.basic_portal_core_classes import _set_default_portal_instantiator
from .._410_swarming_portals import SwarmingPortal


def _instantiate_default_local_portal():
    SwarmingPortal(root_dict = get_default_portal_base_dir())


_set_default_portal_instantiator(_instantiate_default_local_portal)