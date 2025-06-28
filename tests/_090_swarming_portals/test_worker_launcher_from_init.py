from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._090_swarming_portals.swarming_portals import (
    SwarmingPortal)
import pythagoras as pth


def test_launch_background_worker_from_init(tmpdir):

    with _PortalTester(SwarmingPortal
            , tmpdir, max_n_workers=1) as t:

        @pth.pure()
        def sample_f(s:str) -> str:
            return 2*s

        address = sample_f.swarm(s="hello")
        address._invalidate_cache()
        assert address.get() == "hellohello"

