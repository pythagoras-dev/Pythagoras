from pythagoras import SwarmingPortal, pure
from pythagoras import _PortalTester
from pythagoras._010_basic_portals.basic_portal_core_classes import get_description_value_by_key
from pythagoras._090_swarming_portals.swarming_portals import BACKGROUND_WORKERS_TXT


def test_portal(tmpdir):

    with _PortalTester():
        portal = SwarmingPortal(
            root_dict=tmpdir,
            n_background_workers=2)
        description = portal.describe()
        assert description.shape == (11, 3)
        assert get_description_value_by_key(description
            , BACKGROUND_WORKERS_TXT) == 2







