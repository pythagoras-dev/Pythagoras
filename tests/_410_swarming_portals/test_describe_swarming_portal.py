from pythagoras import SwarmingPortal
from pythagoras import _PortalTester
from pythagoras._210_basic_portals.portal_description_helpers import _get_description_value_by_key
from pythagoras._410_swarming_portals.swarming_portals import _MAX_BACKGROUND_WORKERS_TXT


def test_portal(tmpdir):

    with _PortalTester():
        portal = SwarmingPortal(
            root_dict=tmpdir,
            max_n_workers=4)
        description = portal.describe()
        assert description.shape == (15, 3)
        assert _get_description_value_by_key(
            description, _MAX_BACKGROUND_WORKERS_TXT) == portal.max_n_workers







