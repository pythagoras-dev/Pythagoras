from src.pythagoras import SwarmingPortal
from src.pythagoras import _PortalTester
from src.pythagoras._010_basic_portals.basic_portal_class_OLD import get_description_value_by_key
from src.pythagoras._090_swarming_portals.swarming_portals import BACKGROUND_WORKERS_TXT


def test_portal(tmpdir):

    with _PortalTester():
        portal = SwarmingPortal(
            root_dict=tmpdir,
            n_background_workers=2)
        description = portal.describe()
        assert description.shape == (11, 3)
        assert get_description_value_by_key(description
            , BACKGROUND_WORKERS_TXT) == 2







