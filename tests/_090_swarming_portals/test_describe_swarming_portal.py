from pythagoras import SwarmingPortal
from pythagoras import _PortalTester
from pythagoras._010_basic_portals.basic_portal_core_classes import _get_description_value_by_key
from pythagoras._090_swarming_portals.swarming_portals import _BACKGROUND_WORKERS_TXT


def test_portal(tmpdir):

    with _PortalTester():
        portal = SwarmingPortal(
            root_dict=tmpdir,
            max_n_workers=4)
        description = portal.describe()
        assert description.shape == (12, 3)
        assert _get_description_value_by_key(description
            , _BACKGROUND_WORKERS_TXT) == portal.max_n_workers







