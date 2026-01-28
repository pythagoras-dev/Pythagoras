from pythagoras import SwarmingPortal
from pythagoras import _PortalTester


def test_empty_swarming_portal(tmpdir):
    # tmpdir = "TEST_EMPTY_SWARMING_PORTAL"+str(time.time())
    with _PortalTester():
        _portal = SwarmingPortal(
            root_dict=tmpdir,
            exact_n_workers=4)








