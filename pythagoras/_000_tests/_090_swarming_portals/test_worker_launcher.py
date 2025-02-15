from copy import deepcopy
from pythagoras import BasicPortal
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._090_swarming_portals.swarming_portals import (
    SwarmingPortal, _process_random_execution_request)
from pythagoras._080_pure_code_portals.pure_decorator import pure
import pythagoras as pth

def test_launch_background_worker(tmpdir):

    with _PortalTester(SwarmingPortal, tmpdir) as t:
        t.portal._launch_background_worker()

        @pth.pure()
        def f():
            return 5

        address = f.swarm()
        address._invalidate_cache()
        assert address.get() == 5